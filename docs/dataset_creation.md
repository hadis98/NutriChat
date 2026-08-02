# NutriChat Benchmark Construction

## Development benchmark

The 200-question development benchmark was used for system development,
including chunking selection, retrieval experiments, prompt development,
routing, safety improvements, and error analysis. It was therefore treated
only as development data.

## Test benchmark

The 300-question test benchmark was generated with assistance from GPT-5.6.
The complete nutrition textbook and the existing 200-question development
benchmark were supplied to the model.

The generation prompt required the model to:

- produce 300 new questions;
- avoid exact and semantic overlap with the development benchmark;
- derive answerable questions and reference answers from the textbook;
- avoid testing questions against NutriChat;
- follow predefined category, question-type, difficulty, and safety
  distributions;
- assign expected textbook pages;
- preserve the predefined JSON schema; and
- perform internal consistency checks before returning the dataset.

The complete generation prompt is available at:

`prompts/test_dataset_creation_prompt.txt`

## Test-set independence

The test benchmark was not used during the original selection of chunking,
retrieval, reranking, candidate-k, or final-context configurations.

