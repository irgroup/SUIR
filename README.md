# Context-Driven Interactive Query Simulations Based on Generative Large Language Models
This repository accompanies our ECIR'24 full paper entitled _"Context-Driven Interactive Query Simulations Based on Generative Large Language Models"_. It contains the code and results to make the experiments transparent and reproducible. All of the experiments can be reproduced with the help of the source code and the Jupyter notebooks. Besides, we also provide the generated resources like queries or simulated interaction logs in the subdirectories.

## Publication
The author's version of the work can be found on the [arXiv](https://arxiv.org/abs/2312.09631). Please cite the work as follows:
```
@misc{engelmann2023contextdriven,
      title={Context-Driven Interactive Query Simulations Based on Generative Large Language Models}, 
      author={Björn Engelmann and Timo Breuer and Jana Isabelle Friese and Philipp Schaer and Norbert Fuhr},
      year={2023},
      eprint={2312.09631},
      archivePrefix={arXiv},
      primaryClass={cs.IR}
}
```

## Query datasets
- [Doc2Query dataset](./simulation/data/d2qs_clean)
- [GPT-3.5 dataset (Core17)](./simulation/data/nyt)
- [GPT-3.5 dataset (Core18)](./simulation/data/wapo)

## Directory 
| Directory | Description |
| --- | --- |
| `api_server/` | This directory contains the REST-API to the retrieval engine of our experiments. |
| `simulation/` | This directory contains the source code and configuration files of our simulation experiments. Besides, it contains the simulated session logs and the query datasets. |
