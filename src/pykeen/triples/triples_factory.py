# -*- coding: utf-8 -*-

"""Implementation of basic instance factory which creates just instances based on standard KG triples."""
import logging
import os
import re
from collections import defaultdict
from typing import Callable, Collection, Dict, Iterable, List, Mapping, Optional, Sequence, Set, TextIO, Tuple, Union

import numpy as np
import pandas as pd
import torch
from tqdm.autonotebook import tqdm

from .instances import LCWAInstances, SLCWAInstances
from .utils import load_triples
from ..typing import EntityMapping, LabeledTriples, MappedTriples, RelationMapping
from ..utils import compact_mapping, invert_mapping, random_non_negative_int, slice_triples

__all__ = [
    'TriplesFactory',
    'create_entity_mapping',
    'create_relation_mapping',
    'INVERSE_SUFFIX',
]

logger = logging.getLogger(__name__)

INVERSE_SUFFIX = '_inverse'
TRIPLES_DF_COLUMNS = ('head_id', 'head_label', 'relation_id', 'relation_label', 'tail_id', 'tail_label')


def get_unique_entity_ids_from_triples_tensor(mapped_triples: MappedTriples) -> torch.LongTensor:
    """Return the unique entity IDs used in a tensor of triples."""
    return mapped_triples[:, [0, 2]].unique()


def _create_multi_label_tails_instance(
    mapped_triples: MappedTriples,
    use_tqdm: Optional[bool] = None,
) -> Dict[Tuple[int, int], List[int]]:
    """Create for each (h,r) pair the multi tail label."""
    logger.debug('Creating multi label tails instance')

    '''
    The mapped triples matrix has to be a numpy array to ensure correct pair hashing, as explained in
    https://github.com/pykeen/pykeen/commit/1bc71fe4eb2f24190425b0a4d0b9d6c7b9c4653a
    '''
    mapped_triples = mapped_triples.cpu().detach().numpy()

    s_p_to_multi_tails_new = _create_multi_label_instances(
        mapped_triples,
        element_1_index=0,
        element_2_index=1,
        label_index=2,
        use_tqdm=use_tqdm,
    )

    logger.debug('Created multi label tails instance')

    return s_p_to_multi_tails_new


def _create_multi_label_instances(
    mapped_triples: MappedTriples,
    element_1_index: int,
    element_2_index: int,
    label_index: int,
    use_tqdm: Optional[bool] = None,
) -> Dict[Tuple[int, int], List[int]]:
    """Create for each (element_1, element_2) pair the multi-label."""
    instance_to_multi_label = defaultdict(set)

    if use_tqdm is None:
        use_tqdm = True

    it = mapped_triples
    if use_tqdm:
        it = tqdm(mapped_triples, unit='triple', unit_scale=True, desc='Grouping triples')
    for row in it:
        instance_to_multi_label[row[element_1_index], row[element_2_index]].add(row[label_index])

    # Create lists out of sets for proper numpy indexing when loading the labels
    # TODO is there a need to have a canonical sort order here?
    instance_to_multi_label_new = {
        key: list(value)
        for key, value in instance_to_multi_label.items()
    }

    return instance_to_multi_label_new


def create_entity_mapping(triples: LabeledTriples) -> EntityMapping:
    """Create mapping from entity labels to IDs.

    :param triples: shape: (n, 3), dtype: str
    """
    # Split triples
    heads, tails = triples[:, 0], triples[:, 2]
    # Sorting ensures consistent results when the triples are permuted
    entity_labels = sorted(set(heads).union(tails))
    # Create mapping
    return {
        str(label): i
        for (i, label) in enumerate(entity_labels)
    }


def create_relation_mapping(relations: set) -> RelationMapping:
    """Create mapping from relation labels to IDs.

    :param relations: set
    """
    # Sorting ensures consistent results when the triples are permuted
    relation_labels = sorted(
        set(relations),
        key=lambda x: (re.sub(f'{INVERSE_SUFFIX}$', '', x), x.endswith(f'{INVERSE_SUFFIX}')),
    )
    # Create mapping
    return {
        str(label): i
        for (i, label) in enumerate(relation_labels)
    }


def _map_triples_elements_to_ids(
    triples: LabeledTriples,
    entity_to_id: EntityMapping,
    relation_to_id: RelationMapping,
) -> MappedTriples:
    """Map entities and relations to pre-defined ids."""
    if triples.size == 0:
        logger.warning('Provided empty triples to map.')
        return torch.empty(0, 3, dtype=torch.long)

    heads, relations, tails = slice_triples(triples)

    # When triples that don't exist are trying to be mapped, they get the id "-1"
    entity_getter = np.vectorize(entity_to_id.get)
    head_column = entity_getter(heads, [-1])
    tail_column = entity_getter(tails, [-1])
    relation_getter = np.vectorize(relation_to_id.get)
    relation_column = relation_getter(relations, [-1])

    # Filter all non-existent triples
    head_filter = head_column < 0
    relation_filter = relation_column < 0
    tail_filter = tail_column < 0
    num_no_head = head_filter.sum()
    num_no_relation = relation_filter.sum()
    num_no_tail = tail_filter.sum()

    if (num_no_head > 0) or (num_no_relation > 0) or (num_no_tail > 0):
        logger.warning(
            f"You're trying to map triples with {num_no_head + num_no_tail} entities and {num_no_relation} relations"
            f" that are not in the training set. These triples will be excluded from the mapping.",
        )
        non_mappable_triples = (head_filter | relation_filter | tail_filter)
        head_column = head_column[~non_mappable_triples, None]
        relation_column = relation_column[~non_mappable_triples, None]
        tail_column = tail_column[~non_mappable_triples, None]
        logger.warning(
            f"In total {non_mappable_triples.sum():.0f} from {triples.shape[0]:.0f} triples were filtered out",
        )

    triples_of_ids = np.concatenate([head_column, relation_column, tail_column], axis=1)

    triples_of_ids = np.array(triples_of_ids, dtype=np.long)
    # Note: Unique changes the order of the triples
    # Note: Using unique means implicit balancing of training samples
    unique_mapped_triples = np.unique(ar=triples_of_ids, axis=0)
    return torch.tensor(unique_mapped_triples, dtype=torch.long)


class TriplesFactory:
    """Create instances given the path to triples."""

    #: The mapping from entities' labels to their indices
    entity_to_id: EntityMapping

    #: The mapping from relations' labels to their indices
    relation_to_id: RelationMapping

    #: A three-column matrix where each row are the head identifier,
    #: relation identifier, then tail identifier
    mapped_triples: MappedTriples

    #: A dictionary mapping each relation to its inverse, if inverse triples were created
    relation_to_inverse: Optional[Mapping[str, str]]

    #: The mapping from entity IDs to their labels
    entity_id_to_label: Mapping[int, str]

    #: The mapping from relation IDs to their labels
    relation_id_to_label: Mapping[int, str]

    #: A vectorized version of entity_label_to_id; initialized automatically
    # TODO: Type annotation: the additional int parameter is optional
    _vectorized_entity_mapper: Callable[[np.ndarray, Tuple[int]], np.ndarray]

    #: A vectorized version of relation_label_to_id; initialized automatically
    _vectorized_relation_mapper: Callable[[np.ndarray, Tuple[int]], np.ndarray]

    #: A vectorized version of entity_id_to_label; initialized automatically
    _vectorized_entity_labeler: Callable[[np.ndarray, Tuple[str]], np.ndarray]

    #: A vectorized version of relation_id_to_label; initialized automatically
    _vectorized_relation_labeler: Callable[[np.ndarray, Tuple[str]], np.ndarray]

    def __init__(
        self,
        entity_to_id: EntityMapping,
        relation_to_id: RelationMapping,
        mapped_triples: MappedTriples,
        relation_to_inverse: Optional[Mapping[str, str]],
    ):
        self.entity_to_id = entity_to_id
        self.relation_to_id = relation_to_id
        self.mapped_triples = mapped_triples
        self.relation_to_inverse = relation_to_inverse

        # ID to label mapping
        self.entity_id_to_label = invert_mapping(mapping=self.entity_to_id)
        self.relation_id_to_label = invert_mapping(mapping=self.relation_to_id)

        # vectorized versions
        self._vectorized_entity_mapper = np.vectorize(self.entity_to_id.get)
        self._vectorized_relation_mapper = np.vectorize(self.relation_to_id.get)
        self._vectorized_entity_labeler = np.vectorize(self.entity_id_to_label.get)
        self._vectorized_relation_labeler = np.vectorize(self.relation_id_to_label.get)

    @property
    def labeled_triples(self) -> LabeledTriples:
        """A three-column matrix where each row are the head label, relation label, then tail label."""
        return self._label_triples(mapped_triples=self.mapped_triples)

    def _label_triples(self, mapped_triples: MappedTriples) -> LabeledTriples:
        if mapped_triples.numel() == 0:
            return np.empty(shape=(0, 3), dtype=str)
        mapped_triples = mapped_triples.numpy().T
        return np.stack([
            labeler(col)
            for col, labeler in zip(
                mapped_triples,
                (
                    self._vectorized_entity_labeler,
                    self._vectorized_relation_labeler,
                    self._vectorized_entity_labeler,
                )
            )
        ])

    @classmethod
    def from_path(
        cls,
        path: Union[str, TextIO],
        create_inverse_triples: bool = False,
        entity_to_id: Optional[EntityMapping] = None,
        relation_to_id: Optional[RelationMapping] = None,
        compact_id: bool = True,
    ) -> "TriplesFactory":
        """Initialize the triples factory.

        :param path: The path to a 3-column TSV file with triples in it. If not specified,
         you should specify ``triples``.
        :param create_inverse_triples: Should inverse triples be created? Defaults to False.
        :param compact_id:
            Whether to compact the IDs such that they range from 0 to (num_entities or num_relations)-1
        """

        if isinstance(path, str):
            path = os.path.abspath(path)
        elif isinstance(path, TextIO):
            path = os.path.abspath(path.name)
        else:
            raise TypeError(f'path is invalid type: {type(path)}')

        # TODO: Check if lazy evaluation would make sense
        triples = load_triples(path)

        return TriplesFactory.from_labeled_triples(
            triples=triples,
            create_inverse_triples=create_inverse_triples,
            entity_to_id=entity_to_id,
            relation_to_id=relation_to_id,
            compact_id=compact_id,
        )

    @classmethod
    def from_labeled_triples(
        cls,
        triples: np.ndarray,
        create_inverse_triples: bool = False,
        entity_to_id: Optional[EntityMapping] = None,
        relation_to_id: Optional[RelationMapping] = None,
        compact_id: bool = True,
    ) -> "TriplesFactory":
        """Initialize the triples factory.

        :param triples:
            A 3-column numpy array with triples in it.
        :param create_inverse_triples:
            Should inverse triples be created? Defaults to False.
        :param compact_id:
            Whether to compact the IDs such that they range from 0 to (num_entities or num_relations)-1
        """
        _num_entities = len(set(triples[:, 0]).union(triples[:, 2]))

        relations = triples[:, 1]
        unique_relations = set(relations)

        # Check if the triples are inverted already
        relations_already_inverted = cls._check_already_inverted_relations(unique_relations)

        if create_inverse_triples or relations_already_inverted:
            create_inverse_triples = True
            if relations_already_inverted:
                logger.info(
                    f'Some triples already have suffix {INVERSE_SUFFIX}. '
                    f'Creating TriplesFactory based on inverse triples',
                )
                relation_to_inverse = {
                    re.sub('_inverse$', '', relation): f"{re.sub('_inverse$', '', relation)}{INVERSE_SUFFIX}"
                    for relation in unique_relations
                }

            else:
                relation_to_inverse = {
                    relation: f"{relation}{INVERSE_SUFFIX}"
                    for relation in unique_relations
                }
                inverse_triples = np.stack(
                    [
                        triples[:, 2],
                        np.array([relation_to_inverse[relation] for relation in relations], dtype=np.str),
                        triples[:, 0],
                    ],
                    axis=-1,
                )
                # extend original triples with inverse ones
                triples = np.concatenate([triples, inverse_triples], axis=0)
                _num_relations = 2 * len(unique_relations)

        else:
            create_inverse_triples = False
            relation_to_inverse = None
            _num_relations = len(unique_relations)

        # Generate entity mapping if necessary
        if entity_to_id is None:
            entity_to_id = create_entity_mapping(triples=triples)
        if compact_id:
            entity_to_id = compact_mapping(mapping=entity_to_id)[0]
        entity_to_id = entity_to_id

        # Generate relation mapping if necessary
        if relation_to_id is None:
            if create_inverse_triples:
                relation_to_id = create_relation_mapping(
                    set(relation_to_inverse.keys()).union(set(relation_to_inverse.values())),
                )
            else:
                relation_to_id = create_relation_mapping(unique_relations)
        if compact_id:
            relation_to_id = compact_mapping(mapping=relation_to_id)[0]
        relation_to_id = relation_to_id

        # Map triples of labels to triples of IDs.
        mapped_triples = _map_triples_elements_to_ids(
            triples=triples,
            entity_to_id=entity_to_id,
            relation_to_id=relation_to_id,
        )

        return TriplesFactory(
            entity_to_id=entity_to_id,
            relation_to_id=relation_to_id,
            mapped_triples=mapped_triples,
            relation_to_inverse=relation_to_inverse,
        )

    @property
    def num_entities(self) -> int:  # noqa: D401
        """The number of unique entities."""
        return len(self.entity_to_id)

    @property
    def num_relations(self) -> int:  # noqa: D401
        """The number of unique relations."""
        return len(self.relation_to_id)

    @property
    def num_triples(self) -> int:  # noqa: D401
        """The number of triples."""
        return self.mapped_triples.shape[0]

    @property
    def create_inverse_triples(self) -> bool:  # noqa: D401
        """Whether the triples factory contains inverse triples."""
        return self.relation_to_inverse is not None

    def get_inverse_relation_id(self, relation: str) -> int:
        """Get the inverse relation identifier for the given relation."""
        if self.relation_to_inverse is None:
            raise ValueError('Can not get inverse triple, they have not been created.')
        inverse_relation = self.relation_to_inverse[relation]
        return self.relation_to_id[inverse_relation]

    def extra_repr(self) -> str:
        return f"num_triples={self.num_triples}, num_entities={self.num_entities}, num_relations={self.num_relations}"

    def __repr__(self):  # noqa: D105
        return f'{self.__class__.__name__}({self.extra_repr()})'

    @staticmethod
    def _check_already_inverted_relations(relations: Iterable[str]) -> bool:
        for relation in relations:
            if relation.endswith(INVERSE_SUFFIX):
                # We can terminate the search after finding the first inverse occurrence
                return True

        return False

    def create_slcwa_instances(self) -> SLCWAInstances:
        """Create sLCWA instances for this factory's triples."""
        return SLCWAInstances(
            mapped_triples=self.mapped_triples,
            entity_to_id=self.entity_to_id,
            relation_to_id=self.relation_to_id,
        )

    def create_lcwa_instances(self, use_tqdm: Optional[bool] = None) -> LCWAInstances:
        """Create LCWA instances for this factory's triples."""
        s_p_to_multi_tails = _create_multi_label_tails_instance(
            mapped_triples=self.mapped_triples,
            use_tqdm=use_tqdm,
        )
        sp, multi_o = zip(*s_p_to_multi_tails.items())
        mapped_triples: torch.LongTensor = torch.tensor(sp, dtype=torch.long)
        labels = np.array([np.array(item) for item in multi_o], dtype=object)

        return LCWAInstances(
            mapped_triples=mapped_triples,
            entity_to_id=self.entity_to_id,
            relation_to_id=self.relation_to_id,
            labels=labels,
        )

    def map_triples_to_id(self, triples: Union[str, LabeledTriples]) -> MappedTriples:
        """Load triples and map to ids based on the existing id mappings of the triples factory.

        Works from either the path to a file containing triples given as string or a numpy array containing triples.
        """
        if isinstance(triples, str):
            triples = load_triples(triples)
        # Ensure 2d array in case only one triple was given
        triples = np.atleast_2d(triples)
        # FIXME this function is only ever used in tests
        return _map_triples_elements_to_ids(
            triples=triples,
            entity_to_id=self.entity_to_id,
            relation_to_id=self.relation_to_id,
        )

    def split(
        self,
        ratios: Union[float, Sequence[float]] = 0.8,
        *,
        random_state: Union[None, int] = None,
        randomize_cleanup: bool = False,
    ) -> List['TriplesFactory']:
        """Split a triples factory into a train/test.

        :param ratios: There are three options for this argument. First, a float can be given between 0 and 1.0,
         non-inclusive. The first triples factory will get this ratio and the second will get the rest. Second,
         a list of ratios can be given for which factory in which order should get what ratios as in ``[0.8, 0.1]``.
         The final ratio can be omitted because that can be calculated. Third, all ratios can be explicitly set in
         order such as in ``[0.8, 0.1, 0.1]`` where the sum of all ratios is 1.0.
        :param random_state: The random state used to shuffle and split the triples in this factory.
        :param randomize_cleanup: If true, uses the non-deterministic method for moving triples to the training set.
         This has the advantage that it doesn't necessarily have to move all of them, but it might be slower.

        .. code-block:: python

            ratio = 0.8  # makes a [0.8, 0.2] split
            training_factory, testing_factory = factory.split(ratio)

            ratios = [0.8, 0.1]  # makes a [0.8, 0.1, 0.1] split
            training_factory, testing_factory, validation_factory = factory.split(ratios)

            ratios = [0.8, 0.1, 0.1]  # also makes a [0.8, 0.1, 0.1] split
            training_factory, testing_factory, validation_factory = factory.split(ratios)
        """
        # Prepare split index
        if isinstance(ratios, float):
            ratios = [ratios]

        ratio_sum = sum(ratios)
        if ratio_sum == 1.0:
            ratios = ratios[:-1]  # avoid rounding issues
        elif ratio_sum > 1.0:
            raise ValueError(f'ratios sum to more than 1.0: {ratios} (sum={ratio_sum})')

        # convert to absolute sizes
        n_triples = self.num_triples
        sizes = [
            int(split_ratio * n_triples)
            for split_ratio in ratios
        ]
        assert sum(sizes) <= n_triples
        sizes = sizes + [n_triples - sum(sizes)]

        # Prepare shuffle index
        if random_state is None:
            random_state = random_non_negative_int()
            logger.warning(f'Using random_state={random_state} to split {self}')
        torch.manual_seed(seed=random_state)
        index = torch.randperm(n_triples)

        # Split triples
        triples_groups = [
            self.mapped_triples[idx]
            for idx in torch.split(index, split_size_or_sections=sizes, dim=0)
        ]
        logger.info(
            'done splitting triples to groups of sizes %s',
            [triples.shape[0] for triples in triples_groups],
        )

        # Make sure that the first element has all the right stuff in it
        logger.debug('cleaning up groups')
        triples_groups = _tf_cleanup_all(
            triples_groups,
            seed=random_state if randomize_cleanup else None,
        )
        logger.debug('done cleaning up groups')

        for i, (triples, exp_size, exp_ratio) in enumerate(zip(triples_groups, sizes, ratios)):
            actual_size = triples.shape[0]
            actual_ratio = actual_size / exp_size * exp_ratio
            if actual_size != exp_size:
                logger.warning(
                    f'Requested ratio[{i}]={exp_ratio:.3f} (equal to size {exp_size}), but got {actual_ratio:.3f} '
                    f'(equal to size {actual_size}) to ensure that all entities/relations occur in train.',
                )

        # Make new triples factories for each group
        return [
            TriplesFactory(
                entity_to_id=self.entity_to_id,
                relation_to_id=self.relation_to_id,
                mapped_triples=mapped_triples,
                relation_to_inverse=self.relation_to_inverse,
            )
            for mapped_triples in triples_groups
        ]

    def get_most_frequent_relation_ids(self, n: Union[int, float]) -> Set[int]:
        """Get the n most frequent relations.

        :param n:
            Either the (integer) number of top relations to keep or the (float) percentage of top
            relationships to keep.
        """
        logger.info(f'applying cutoff of {n} to {self}')
        if isinstance(n, float):
            assert 0 < n < 1
            n = int(self.num_relations * n)
        elif not isinstance(n, int):
            raise TypeError('n must be either an integer or a float')

        uniq, counts = torch.unique(self.mapped_triples, return_counts=True)
        top_idx = counts.topk(k=n, largest=True, sorted=True)
        return set(uniq[top_idx].tolist())

    def get_most_frequent_relations(self, n: Union[int, float]) -> Set[str]:
        """Get the n most frequent relations.

        :param n: Either the (integer) number of top relations to keep or the (float) percentage of top relationships
         to keep
        """
        return set(self.relation_id_to_label[idx] for idx in self.get_most_frequent_relation_ids(n=n))

    def get_mask_for_entities(self, entities: Collection[str], invert: bool = False) -> torch.BoolTensor:
        """Get mask for triples with the given entities."""
        entity_ids = torch.as_tensor(data=[self.entity_to_id[entity] for entity in entities])
        return _torch_is_in_1d(
            a=self.mapped_triples[:, [0, 2]],
            b=entity_ids,
            invert=invert,
        ).all(dim=-1)

    def get_mask_for_relations(self, relations: Collection[Union[str, int]], invert: bool = False) -> torch.BoolTensor:
        """Get mask for triples with the given relations."""
        # normalize relations
        relations = [
            relation if isinstance(relation, int) else self.relation_to_id[relation]
            for relation in relations
        ]
        relation_ids = torch.as_tensor(data=relations)
        return _torch_is_in_1d(
            a=self.mapped_triples[:, 1],
            b=relation_ids,
            invert=invert,
        )

    def get_triples_for_relations(self, relations: Collection[Union[str, int]], invert: bool = False) -> MappedTriples:
        """Get the labeled triples containing the given relations."""
        mask = self.get_mask_for_relations(relations, invert=invert)
        return self.mapped_triples[mask]

    def _new_from_triples_mask(self, mask: torch.BoolTensor) -> 'TriplesFactory':
        logger.info(f'Keeping {mask.sum()}/{self.num_triples} triples.')
        return TriplesFactory(
            entity_to_id=self.entity_to_id,
            relation_to_id=self.relation_to_id,
            mapped_triples=self.mapped_triples[mask],
            relation_to_inverse=self.relation_to_inverse,
        )

    def new_with_relations(self, relations: Collection[Union[str, int]]) -> 'TriplesFactory':
        """Make a new triples factory only keeping the given relations."""
        logger.info(f'Keeping {len(relations)}/{self.num_relations} relations.')
        mask = self.get_mask_for_relations(relations)
        return self._new_from_triples_mask(mask=mask)

    def new_without_relations(self, relations: Collection[Union[str, int]]) -> 'TriplesFactory':
        """Make a new triples factory without the given relations."""
        logger.info(f'Removing {len(relations)}/{self.num_relations} relations.')
        mask = self.get_mask_for_relations(relations, invert=True)
        return self._new_from_triples_mask(mask=mask)

    def entity_word_cloud(self, top: Optional[int] = None):
        """Make a word cloud based on the frequency of occurrence of each entity in a Jupyter notebook.

        :param top: The number of top entities to show. Defaults to 100.

        .. warning::

            This function requires the ``word_cloud`` package. Use ``pip install pykeen[plotting]`` to
            install it automatically, or install it yourself with
            ``pip install git+https://github.com/kavgan/word_cloud.git``.
        """
        # TODO: this seems rather inefficient, since the word cloud likely then counts the occurrences again
        text = [f'{h} {t}' for h, t in self._vectorized_entity_labeler(self.mapped_triples[:, [0, 2]].numpy())]
        return self._word_cloud(text=text, top=top or 100)

    def relation_word_cloud(self, top: Optional[int] = None):
        """Make a word cloud based on the frequency of occurrence of each relation in a Jupyter notebook.

        :param top: The number of top relations to show. Defaults to 100.

        .. warning::

            This function requires the ``word_cloud`` package. Use ``pip install pykeen[plotting]`` to
            install it automatically, or install it yourself with
            ``pip install git+https://github.com/kavgan/word_cloud.git``.
        """
        text = self._vectorized_relation_labeler(self.mapped_triples[:, 1].numpy()).tolist()
        return self._word_cloud(text=text, top=top or 100)

    def _word_cloud(self, *, text: List[str], top: int):
        try:
            from word_cloud.word_cloud_generator import WordCloud
        except ImportError:
            logger.warning(
                'Could not import module `word_cloud`. '
                'Try installing it with `pip install git+https://github.com/kavgan/word_cloud.git`',
            )
            return

        from IPython.core.display import HTML
        word_cloud = WordCloud()
        return HTML(word_cloud.get_embed_code(text=text, topn=top))

    def tensor_to_df(
        self,
        tensor: torch.LongTensor,
        **kwargs: Union[torch.Tensor, np.ndarray, Sequence],
    ) -> pd.DataFrame:
        """Take a tensor of triples and make a pandas dataframe with labels.

        :param tensor: shape: (n, 3)
            The triples, ID-based and in format (head_id, relation_id, tail_id).
        :param kwargs:
            Any additional number of columns. Each column needs to be of shape (n,). Reserved column names:
            {"head_id", "head_label", "relation_id", "relation_label", "tail_id", "tail_label"}.
        :return:
            A dataframe with n rows, and 6 + len(kwargs) columns.
        """
        # Input validation
        additional_columns = set(kwargs.keys())
        forbidden = additional_columns.intersection(TRIPLES_DF_COLUMNS)
        if len(forbidden) > 0:
            raise ValueError(
                f'The key-words for additional arguments must not be in {TRIPLES_DF_COLUMNS}, but {forbidden} were '
                f'used.',
            )

        # convert to numpy
        tensor = tensor.cpu().numpy()
        data = dict(zip(['head_id', 'relation_id', 'tail_id'], tensor.T))

        # vectorized label lookup
        for column, id_to_label in dict(
            head=self._vectorized_entity_labeler,
            relation=self._vectorized_relation_labeler,
            tail=self._vectorized_entity_labeler,
        ).items():
            data[f'{column}_label'] = id_to_label(data[f'{column}_id'])

        # Additional columns
        for key, values in kwargs.items():
            # convert PyTorch tensors to numpy
            if torch.is_tensor(values):
                values = values.cpu().numpy()
            data[key] = values

        # convert to dataframe
        rv = pd.DataFrame(data=data)

        # Re-order columns
        columns = list(TRIPLES_DF_COLUMNS) + sorted(set(rv.columns).difference(TRIPLES_DF_COLUMNS))
        return rv.loc[:, columns]

    def new_with_restriction(
        self,
        entities: Optional[Collection[str]] = None,
        relations: Optional[Collection[str]] = None,
    ) -> 'TriplesFactory':
        """Make a new triples factory only keeping the given entities and relations, but keeping the ID mapping.

        :param entities:
            The entities of interest. If None, defaults to all entities.
        :param relations:
            The relations of interest. If None, defaults to all relations.

        :return:
            A new triples factory, which has only a subset of the triples containing the entities and relations of
            interest. The label-to-ID mapping is *not* modified.
        """
        if self.create_inverse_triples and relations is not None:
            logger.info(
                'Since %s already contain inverse relations, the relation filter is expanded to contain the inverse '
                'relations as well.',
                str(self),
            )
            relations = list(relations) + list(map(self.relation_to_inverse.__getitem__, relations))

        keep_mask = None

        # Filter for entities
        if entities is not None:
            keep_mask = self.get_mask_for_entities(entities=entities)
            logger.info('Keeping %d/%d entities', len(entities), self.num_entities)

        # Filter for relations
        if relations is not None:
            relation_mask = self.get_mask_for_relations(relations=relations)
            logger.info('Keeping %d/%d relations', len(relations), self.num_relations)
            keep_mask = relation_mask if keep_mask is None else keep_mask & relation_mask

        # No filtering happened
        if keep_mask is None:
            return self

        logger.info('Keeping %d/%d triples', keep_mask.sum(), self.num_triples)
        factory = TriplesFactory(
            entity_to_id=self.entity_to_id,
            relation_to_id=self.relation_to_id,
            mapped_triples=self.mapped_triples[keep_mask],
            relation_to_inverse=self.relation_to_inverse,
        )

        return factory


def _tf_cleanup_all(
    triples_groups: List[MappedTriples],
    *,
    seed: Union[None, int] = None,
) -> List[MappedTriples]:
    """Cleanup a list of triples array with respect to the first array."""
    reference, *others = triples_groups
    rv = []
    for other in others:
        if seed is not None:
            reference, other = _tf_cleanup_randomized(reference, other, seed)
        else:
            reference, other = _tf_cleanup_deterministic(reference, other)
        rv.append(other)
    return [reference, *rv]


def _tf_cleanup_deterministic(training: MappedTriples, testing: MappedTriples) -> Tuple[MappedTriples, MappedTriples]:
    """Cleanup a triples array (testing) with respect to another (training)."""
    move_id_mask = _prepare_cleanup(training, testing)

    training = torch.cat([training, testing[move_id_mask]], dim=0)
    testing = testing[~move_id_mask]

    return training, testing


def _tf_cleanup_randomized(
    training: MappedTriples,
    testing: MappedTriples,
    seed: Union[None, int] = None,
) -> Tuple[MappedTriples, MappedTriples]:
    """Cleanup a triples array, but randomly select testing triples and recalculate to minimize moves.

    1. Calculate ``move_id_mask`` as in :func:`_tf_cleanup_deterministic`
    2. Choose a triple to move, recalculate move_id_mask
    3. Continue until move_id_mask has no true bits
    """
    if seed is None:
        seed = random_non_negative_int()
        logger.warning('Using random_state=%s', seed)
    torch.manual_seed(seed)

    move_id_mask = _prepare_cleanup(training, testing)

    # While there are still triples that should be moved to the training set
    while move_id_mask.any():
        # Pick a random triple to move over to the training triples
        candidates, = move_id_mask.nonzero(as_tuple=True)
        idx = candidates[torch.randint(candidates.shape[0], size=(1,), device=candidates.device)]
        training = torch.cat([training, testing[idx].view(1, -1)])

        # Recalculate the testing triples without that index
        testing = torch.cat([testing[:idx], testing[idx + 1:]])

        # Recalculate the training entities, testing entities, to_move, and move_id_mask
        move_id_mask = _prepare_cleanup(training, testing)

    return training, testing


def _torch_is_in_1d(
    a: torch.Tensor,
    b: torch.Tensor,
    invert: bool = False
) -> torch.BoolTensor:
    if a.numel() == 0 or b.numel() == 0:
        return a.new_zeros(a.shape, dtype=torch.bool)
    max_id = max(a.max(), b.max())
    # TODO: This may require significant amount of memory for large max_id
    mask = a.new_zeros(max_id + 1, dtype=torch.bool)
    mask[b] = True
    result = mask.index_select(dim=0, index=a.view(-1)).view(*a.shape)
    if invert:
        result = ~result
    return result


def _prepare_cleanup(training: MappedTriples, testing: MappedTriples) -> MappedTriples:
    to_move_mask = None
    for col in [[0, 2], 1]:
        training_ids, test_ids = [triples[:, col].view(-1).unique() for triples in [training, testing]]
        to_move = test_ids[~_torch_is_in_1d(test_ids, training_ids)]
        this_to_move_mask = _torch_is_in_1d(testing[:, col], to_move)
        if this_to_move_mask.ndimension() > 1:
            this_to_move_mask = this_to_move_mask.any(dim=1)
        if to_move_mask is None:
            to_move_mask = this_to_move_mask
        else:
            to_move_mask = this_to_move_mask | to_move_mask

    return to_move_mask
