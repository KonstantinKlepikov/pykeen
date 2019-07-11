# -*- coding: utf-8 -*-

"""Training loops for KGE models using multi-modal information."""

import logging
from abc import ABC, abstractmethod
from typing import List, Mapping, Tuple

import numpy as np
import torch.nn as nn
from tqdm import tqdm

from ..instance_creation_factories.instances import Instances
from ..version import get_version

__all__ = [
    'TrainingLoop',
]

log = logging.getLogger(__name__)


class TrainingLoop(ABC):
    def __init__(
            self,
            model: nn.Module,
            optimizer,
            all_entities: np.ndarray = None,
    ) -> None:
        self.model = model
        self.optimizer = optimizer
        self.losses_per_epochs = []
        self.all_entities = all_entities

    @property
    def device(self):
        return self.model.device

    @abstractmethod
    def train(
            self,
            training_instances: Instances,
            num_epochs,
            batch_size,
    ) -> Tuple[nn.Module, List[float]]:
        """Train the KGE model.

        :return: A pair of the KGE model and the losses per epoch.
        """

    def _get_entity_to_vector_dict(self) -> Mapping:
        raise NotImplementedError

    def to_embeddingdb(self, session=None, use_tqdm: bool = False):
        """Upload to the embedding database.

        :param session: Optional SQLAlchemy session
        :param use_tqdm: Use :mod:`tqdm` progress bar?
        :rtype: embeddingdb.sql.models.Collection
        """
        from embeddingdb.sql.models import Embedding, Collection

        if session is None:
            from embeddingdb.sql.models import get_session
            session = get_session()

        collection = Collection(
            package_name='poem',
            package_version=get_version(),
            dimensions=...,
            extras=...,
        )

        it = self._get_entity_to_vector_dict().items()
        if use_tqdm:
            it = tqdm(it, desc='Building SQLAlchemy models')
        for curie, vector in it:
            embedding = Embedding(
                collection=collection,
                curie=curie,
                vector=vector,
            )
            session.add(embedding)
        session.add(collection)
        session.commit()
        return collection