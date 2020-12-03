<p align="center">
  <img src="docs/source/logo.png" height="150">
</p>

<h1 align="center">
  PyKEEN
</h1>

<p align="center">
  <a href="https://github.com/pykeen/pykeen/actions">
    <img src="https://github.com/pykeen/pykeen/workflows/Tests/badge.svg"
         alt="GitHub Actions">
  </a>

  <a href="https://ci.appveyor.com/project/pykeen/pykeen/branch/master">
    <img src="https://ci.appveyor.com/api/projects/status/lwp9cfnsa8d5yx62/branch/master?svg=true"
         alt="AppVeyor">
  </a>

  <a href='https://opensource.org/licenses/MIT'>
    <img src='https://img.shields.io/badge/License-MIT-blue.svg' alt='License'/>
  </a>

  <a href="https://zenodo.org/badge/latestdoi/242672435">
    <img src="https://zenodo.org/badge/242672435.svg" alt="DOI">
  </a>

  <a href="https://optuna.org">
    <img src="https://img.shields.io/badge/Optuna-integrated-blue" alt="Optuna integrated" height="20">
  </a>
</p>

<p align="center">
    <b>PyKEEN</b> (<b>P</b>ython <b>K</b>nowl<b>E</b>dge <b>E</b>mbeddi<b>N</b>gs) is a Python package designed to
    train and evaluate knowledge graph embedding models (incorporating multi-modal information).
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#datasets-20">Datasets</a> •
  <a href="#models-23">Models</a> •
  <a href="#supporters">Support</a> •
  <a href="#citation">Citation</a>
</p>

## Installation ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pykeen) ![PyPI](https://img.shields.io/pypi/v/pykeen)

The latest stable version of PyKEEN can be downloaded and installed from
[PyPI](https://pypi.org/project/pykeen) with:

```bash
$ pip install pykeen
```

The latest version of PyKEEN can be installed directly from the
source on [GitHub](https://github.com/pykeen/pykeen) with:

```bash
pip install git+https://github.com/pykeen/pykeen.git
```

More information about installation (e.g., development mode, Windows installation, extras)
can be found in the [installation documentation](https://pykeen.readthedocs.io/en/latest/installation.html).

## Quickstart [![Documentation Status](https://readthedocs.org/projects/pykeen/badge/?version=latest)](https://pykeen.readthedocs.io/en/latest/?badge=latest)

This example shows how to train a model on a dataset and test on another dataset.

The fastest way to get up and running is to use the pipeline function. It
provides a high-level entry into the extensible functionality of this package.
The following example shows how to train and evaluate the [TransE](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.TransE.html#pykeen.models.TransE)
model on the [Nations](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.Nations.html#pykeen.datasets.Nations)
dataset. By default, the training loop uses the [stochastic local closed world assumption (sLCWA)](https://pykeen.readthedocs.io/en/latest/reference/training.html#pykeen.training.SLCWATrainingLoop)
training approach and evaluates with [rank-based evaluation](https://pykeen.readthedocs.io/en/latest/reference/evaluation/rank_based.html#pykeen.evaluation.RankBasedEvaluator).

```python
from pykeen.pipeline import pipeline

result = pipeline(
    model='TransE',
    dataset='nations',
)
```

The results are returned in an instance of the [PipelineResult](https://pykeen.readthedocs.io/en/latest/reference/pipeline.html#pykeen.pipeline.PipelineResult)
dataclass that has attributes for the trained model, the training loop, the evaluation, and more. See the tutorials on
[understanding the evaluation](https://pykeen.readthedocs.io/en/latest/tutorial/understanding_evaluation.html)
and [making novel link predictions](https://pykeen.readthedocs.io/en/latest/tutorial/making_predictions.html).

PyKEEN is extensible such that:

- Each model has the same API, so anything from ``pykeen.models`` can be dropped in
- Each training loop has the same API, so ``pykeen.training.LCWATrainingLoop`` can be dropped in
- Triples factories can be generated by the user with ``from pykeen.triples.TriplesFactory``

The full documentation can be found at https://pykeen.readthedocs.io.

## Implementation

Below are the models, datasets, training modes, evaluators, and metrics implemented
in ``pykeen``.

### Datasets (20)

| Name          | Reference                                                                                                         | Description                                                                                       |
|---------------|-------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| codexlarge    | [`pykeen.datasets.CoDExLarge`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.CoDExLarge.html)       | The CoDEx large dataset.                                                                          |
| codexmedium   | [`pykeen.datasets.CoDExMedium`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.CoDExMedium.html)     | The CoDEx medium dataset.                                                                         |
| codexsmall    | [`pykeen.datasets.CoDExSmall`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.CoDExSmall.html)       | The CoDEx small dataset.                                                                          |
| conceptnet    | [`pykeen.datasets.ConceptNet`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.ConceptNet.html)       | The ConceptNet dataset.                                                                           |
| drkg          | [`pykeen.datasets.DRKG`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.DRKG.html)                   | The DRKG dataset.                                                                                 |
| fb15k         | [`pykeen.datasets.FB15k`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.FB15k.html)                 | The FB15k dataset.                                                                                |
| fb15k237      | [`pykeen.datasets.FB15k237`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.FB15k237.html)           | The FB15k-237 dataset.                                                                            |
| hetionet      | [`pykeen.datasets.Hetionet`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.Hetionet.html)           | The Hetionet dataset is a large biological network.                                               |
| kinships      | [`pykeen.datasets.Kinships`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.Kinships.html)           | The Kinships dataset.                                                                             |
| nations       | [`pykeen.datasets.Nations`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.Nations.html)             | The Nations dataset.                                                                              |
| ogbbiokg      | [`pykeen.datasets.OGBBioKG`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.OGBBioKG.html)           | The OGB BioKG dataset.                                                                            |
| ogbwikikg     | [`pykeen.datasets.OGBWikiKG`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.OGBWikiKG.html)         | The OGB WikiKG dataset.                                                                           |
| openbiolink   | [`pykeen.datasets.OpenBioLink`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.OpenBioLink.html)     | The OpenBioLink dataset.                                                                          |
| openbiolinkf1 | [`pykeen.datasets.OpenBioLinkF1`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.OpenBioLinkF1.html) | The PyKEEN First Filtered OpenBioLink 2020 Dataset.                                               |
| openbiolinkf2 | [`pykeen.datasets.OpenBioLinkF2`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.OpenBioLinkF2.html) | The PyKEEN Second Filtered OpenBioLink 2020 Dataset.                                              |
| openbiolinklq | [`pykeen.datasets.OpenBioLinkLQ`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.OpenBioLinkLQ.html) | The low-quality variant of the OpenBioLink dataset.                                               |
| umls          | [`pykeen.datasets.UMLS`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.UMLS.html)                   | The UMLS dataset.                                                                                 |
| wn18          | [`pykeen.datasets.WN18`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.WN18.html)                   | The WN18 dataset.                                                                                 |
| wn18rr        | [`pykeen.datasets.WN18RR`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.WN18RR.html)               | The WN18-RR dataset.                                                                              |
| yago310       | [`pykeen.datasets.YAGO310`](https://pykeen.readthedocs.io/en/latest/api/pykeen.datasets.YAGO310.html)             | The YAGO3-10 dataset is a subset of YAGO3 that only contains entities with at least 10 relations. |

### Models (23)

| Name                | Reference                                                                                                                 | Citation                     |
|---------------------|---------------------------------------------------------------------------------------------------------------------------|------------------------------|
| ComplEx             | [`pykeen.models.ComplEx`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ComplEx.html)                         | Trouillon *et al.*, 2016     |
| ComplExLiteral      | [`pykeen.models.ComplExLiteral`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ComplExLiteral.html)           | Agustinus *et al.*, 2018     |
| ConvE               | [`pykeen.models.ConvE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ConvE.html)                             | Dettmers *et al.*, 2018      |
| ConvKB              | [`pykeen.models.ConvKB`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ConvKB.html)                           | Nguyen *et al.*, 2018        |
| DistMult            | [`pykeen.models.DistMult`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.DistMult.html)                       | Yang *et al.*, 2014          |
| DistMultLiteral     | [`pykeen.models.DistMultLiteral`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.DistMultLiteral.html)         | Agustinus *et al.*, 2018     |
| ERMLP               | [`pykeen.models.ERMLP`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ERMLP.html)                             | Dong *et al.*, 2014          |
| ERMLPE              | [`pykeen.models.ERMLPE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ERMLPE.html)                           | Sharifzadeh *et al.*, 2019   |
| HolE                | [`pykeen.models.HolE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.HolE.html)                               | Nickel *et al.*, 2016        |
| KG2E                | [`pykeen.models.KG2E`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.KG2E.html)                               | He *et al.*, 2015            |
| NTN                 | [`pykeen.models.NTN`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.NTN.html)                                 | Socher *et al.*, 2013        |
| ProjE               | [`pykeen.models.ProjE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.ProjE.html)                             | Shi *et al.*, 2017           |
| RESCAL              | [`pykeen.models.RESCAL`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.RESCAL.html)                           | Nickel *et al.*, 2011        |
| RGCN                | [`pykeen.models.RGCN`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.RGCN.html)                               | Schlichtkrull *et al.*, 2018 |
| RotatE              | [`pykeen.models.RotatE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.RotatE.html)                           | Sun *et al.*, 2019           |
| SimplE              | [`pykeen.models.SimplE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.SimplE.html)                           | Kazemi *et al.*, 2018        |
| StructuredEmbedding | [`pykeen.models.StructuredEmbedding`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.StructuredEmbedding.html) | Bordes *et al.*, 2011        |
| TransD              | [`pykeen.models.TransD`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.TransD.html)                           | Ji *et al.*, 2015            |
| TransE              | [`pykeen.models.TransE`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.TransE.html)                           | Bordes *et al.*, 2013        |
| TransH              | [`pykeen.models.TransH`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.TransH.html)                           | Wang *et al.*, 2014          |
| TransR              | [`pykeen.models.TransR`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.TransR.html)                           | Lin *et al.*, 2015           |
| TuckER              | [`pykeen.models.TuckER`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.TuckER.html)                           | Balazevic *et al.*, 2019     |
| UnstructuredModel   | [`pykeen.models.UnstructuredModel`](https://pykeen.readthedocs.io/en/latest/api/pykeen.models.UnstructuredModel.html)     | Bordes *et al.*, 2014        |

### Losses (7)

| Name            | Reference                                                                                                                 | Description                                                                                       |
|-----------------|---------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| bceaftersigmoid | [`pykeen.losses.BCEAfterSigmoidLoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.BCEAfterSigmoidLoss.html) | A loss function which uses the numerically unstable version of explicit Sigmoid + BCE.            |
| bcewithlogits   | [`pykeen.losses.BCEWithLogitsLoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.BCEWithLogitsLoss.html)     | A wrapper around the numeric stable version of the PyTorch binary cross entropy loss.             |
| crossentropy    | [`pykeen.losses.CrossEntropyLoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.CrossEntropyLoss.html)       | Evaluate cross entropy after softmax output.                                                      |
| marginranking   | [`pykeen.losses.MarginRankingLoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.MarginRankingLoss.html)     | A wrapper around the PyTorch margin ranking loss.                                                 |
| mse             | [`pykeen.losses.MSELoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.MSELoss.html)                         | A wrapper around the PyTorch mean square error loss.                                              |
| nssa            | [`pykeen.losses.NSSALoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.NSSALoss.html)                       | An implementation of the self-adversarial negative sampling loss function proposed by [sun2019]_. |
| softplus        | [`pykeen.losses.SoftplusLoss`](https://pykeen.readthedocs.io/en/latest/api/pykeen.losses.SoftplusLoss.html)               | A loss function for the softplus.                                                                 |

### Regularizers (5)

| Name     | Reference                                                                                                                             | Description                                              |
|----------|---------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| combined | [`pykeen.regularizers.CombinedRegularizer`](https://pykeen.readthedocs.io/en/latest/api/pykeen.regularizers.CombinedRegularizer.html) | A convex combination of regularizers.                    |
| lp       | [`pykeen.regularizers.LpRegularizer`](https://pykeen.readthedocs.io/en/latest/api/pykeen.regularizers.LpRegularizer.html)             | A simple L_p norm based regularizer.                     |
| no       | [`pykeen.regularizers.NoRegularizer`](https://pykeen.readthedocs.io/en/latest/api/pykeen.regularizers.NoRegularizer.html)             | A regularizer which does not perform any regularization. |
| powersum | [`pykeen.regularizers.PowerSumRegularizer`](https://pykeen.readthedocs.io/en/latest/api/pykeen.regularizers.PowerSumRegularizer.html) | A simple x^p based regularizer.                          |
| transh   | [`pykeen.regularizers.TransHRegularizer`](https://pykeen.readthedocs.io/en/latest/api/pykeen.regularizers.TransHRegularizer.html)     | A regularizer for the soft constraints in TransH.        |

### Optimizers (6)

| Name     | Reference                                                                                 | Description                                                             |
|----------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| adadelta | [`torch.optim.Adadelta`](https://pytorch.org/docs/stable/optim.html#torch.optim.Adadelta) | Implements Adadelta algorithm.                                          |
| adagrad  | [`torch.optim.Adagrad`](https://pytorch.org/docs/stable/optim.html#torch.optim.Adagrad)   | Implements Adagrad algorithm.                                           |
| adam     | [`torch.optim.Adam`](https://pytorch.org/docs/stable/optim.html#torch.optim.Adam)         | Implements Adam algorithm.                                              |
| adamax   | [`torch.optim.Adamax`](https://pytorch.org/docs/stable/optim.html#torch.optim.Adamax)     | Implements Adamax algorithm (a variant of Adam based on infinity norm). |
| adamw    | [`torch.optim.AdamW`](https://pytorch.org/docs/stable/optim.html#torch.optim.AdamW)       | Implements AdamW algorithm.                                             |
| sgd      | [`torch.optim.SGD`](https://pytorch.org/docs/stable/optim.html#torch.optim.SGD)           | Implements stochastic gradient descent (optionally with momentum).      |

### Training Loops (2)

| Name   | Reference                                                                                                                                | Description                                                                               |
|--------|------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| lcwa   | [`pykeen.training.LCWATrainingLoop`](https://pykeen.readthedocs.io/en/latest/reference/training.html#pykeen.training.LCWATrainingLoop)   | A training loop that uses the local closed world assumption training approach.            |
| slcwa  | [`pykeen.training.SLCWATrainingLoop`](https://pykeen.readthedocs.io/en/latest/reference/training.html#pykeen.training.SLCWATrainingLoop) | A training loop that uses the stochastic local closed world assumption training approach. |

### Negative Samplers (2)

| Name      | Reference                                                                                                                               | Description                                                                            |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| basic     | [`pykeen.sampling.BasicNegativeSampler`](https://pykeen.readthedocs.io/en/latest/api/pykeen.sampling.BasicNegativeSampler.html)         | A basic negative sampler.                                                              |
| bernoulli | [`pykeen.sampling.BernoulliNegativeSampler`](https://pykeen.readthedocs.io/en/latest/api/pykeen.sampling.BernoulliNegativeSampler.html) | An implementation of the bernoulli negative sampling approach proposed by [wang2014]_. |

### Stoppers (2)

| Name   | Reference                                                                                                                      | Description                   |
|--------|--------------------------------------------------------------------------------------------------------------------------------|-------------------------------|
| early  | [`pykeen.stoppers.EarlyStopper`](https://pykeen.readthedocs.io/en/latest/reference/stoppers.html#pykeen.stoppers.EarlyStopper) | A harness for early stopping. |
| nop    | [`pykeen.stoppers.NopStopper`](https://pykeen.readthedocs.io/en/latest/reference/stoppers.html#pykeen.stoppers.NopStopper)     | A stopper that does nothing.  |

### Evaluators (2)

| Name      | Reference                              | Description                                   |
|-----------|----------------------------------------|-----------------------------------------------|
| rankbased | `pykeen.evaluation.RankBasedEvaluator` | A rank-based evaluator for KGE models.        |
| sklearn   | `pykeen.evaluation.SklearnEvaluator`   | An evaluator that uses a Scikit-learn metric. |

### Metrics (6)

| Metric                  | Description                                                                                                        | Evaluator   | Reference                                  |
|-------------------------|--------------------------------------------------------------------------------------------------------------------|-------------|--------------------------------------------|
| Adjusted Mean Rank      | The mean over all chance-adjusted ranks: mean_i (2r_i / (num_entities+1)). Lower is better.                        | rankbased   | `pykeen.evaluation.RankBasedMetricResults` |
| Average Precision Score | The area under the precision-recall curve, between [0.0, 1.0]. Higher is better.                                   | sklearn     | `pykeen.evaluation.SklearnMetricResults`   |
| Hits At K               | The hits at k for different values of k, i.e. the relative frequency of ranks not larger than k. Higher is better. | rankbased   | `pykeen.evaluation.RankBasedMetricResults` |
| Mean Rank               | The mean over all ranks: mean_i r_i. Lower is better.                                                              | rankbased   | `pykeen.evaluation.RankBasedMetricResults` |
| Mean Reciprocal Rank    | The mean over all reciprocal ranks: mean_i (1/r_i). Higher is better.                                              | rankbased   | `pykeen.evaluation.RankBasedMetricResults` |
| Roc Auc Score           | The area under the ROC curve between [0.0, 1.0]. Higher is better.                                                 | sklearn     | `pykeen.evaluation.SklearnMetricResults`   |

### Trackers (3)

| Name    | Reference                                                                                                                       | Description                       |
|---------|---------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| mlflow  | [`pykeen.trackers.MLFlowResultTracker`](https://pykeen.readthedocs.io/en/latest/api/pykeen.trackers.MLFlowResultTracker.html)   | A tracker for MLflow.             |
| neptune | [`pykeen.trackers.NeptuneResultTracker`](https://pykeen.readthedocs.io/en/latest/api/pykeen.trackers.NeptuneResultTracker.html) | A tracker for Neptune.ai.         |
| wandb   | [`pykeen.trackers.WANDBResultTracker`](https://pykeen.readthedocs.io/en/latest/api/pykeen.trackers.WANDBResultTracker.html)     | A tracker for Weights and Biases. |

## Hyper-parameter Optimization

### Samplers (3)

| Name   | Reference                                                                                                                         | Description                                                     |
|--------|-----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| grid   | [`optuna.samplers.GridSampler`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.samplers.GridSampler.html)     | Sampler using grid search.                                      |
| random | [`optuna.samplers.RandomSampler`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.samplers.RandomSampler.html) | Sampler using random sampling.                                  |
| tpe    | [`optuna.samplers.TPESampler`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.samplers.TPESampler.html)       | Sampler using TPE (Tree-structured Parzen Estimator) algorithm. |

## Experimentation

### Reproduction

PyKEEN includes a set of curated experimental settings for reproducing past landmark
experiments. They can be accessed and run like:

```bash
pykeen experiments reproduce tucker balazevic2019 fb15k
```

Where the three arguments are the model name, the reference, and the dataset.
The output directory can be optionally set with `-d`.

### Ablation

PyKEEN includes the ability to specify ablation studies using the
hyper-parameter optimization module. They can be run like:

```bash
pykeen experiments ablation ~/path/to/config.json
```

## Contributing

Contributions, whether filing an issue, making a pull request, or forking, are appreciated. 
See [CONTRIBUTING.md](/CONTRIBUTING.md) for more information on getting involved.

## Acknowledgements

### Supporters

This project has been supported by several organizations (in alphabetical order):

- [Bayer](https://www.bayer.com/)
- [Enveda Therapeutics](https://envedatherapeutics.com/)
- [Fraunhofer Institute for Algorithms and Scientific Computing](https://www.scai.fraunhofer.de)
- [Fraunhofer Institute for Intelligent Analysis and Information Systems](https://www.iais.fraunhofer.de)
- [Fraunhofer Center for Machine Learning](https://www.cit.fraunhofer.de/de/zentren/maschinelles-lernen.html)
- [Ludwig-Maximilians-Universität München](https://www.en.uni-muenchen.de/index.html)
- [Munich Center for Machine Learning (MCML)](https://mcml.ai/)
- [Siemens](https://new.siemens.com/global/en.html)
- [Smart Data Analytics Research Group (University of Bonn & Fraunhofer IAIS)](https://sda.tech)
- [Technical University of Denmark - DTU Compute - Section for Cognitive Systems](https://www.compute.dtu.dk/english/research/research-sections/cogsys)
- [Technical University of Denmark - DTU Compute - Section for Statistics and Data Analysis](https://www.compute.dtu.dk/english/research/research-sections/stat)
- [University of Bonn](https://www.uni-bonn.de/)

### Logo

The PyKEEN logo was designed by Carina Steinborn.

## Citation

If you have found PyKEEN useful in your work, please consider citing [our article](https://arxiv.org/abs/2007.14175):

```bibtex
@article{ali2020pykeen,
  title={PyKEEN 1.0: A Python Library for Training and Evaluating Knowledge Graph Emebddings},
  author={Ali, Mehdi and Berrendorf, Max and Hoyt, Charles Tapley and Vermue, Laurent and Sharifzadeh, Sahand and Tresp, Volker and Lehmann, Jens},
  journal={arXiv preprint arXiv:2007.14175},
  year={2020}
}
```
