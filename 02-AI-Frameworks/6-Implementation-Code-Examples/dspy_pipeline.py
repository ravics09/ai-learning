"""
dspy_pipeline.py
----------------
Goal: show DSPy's "programming, not prompting" model — declare a Signature, pick a
Module, and (optionally) let an Optimizer compile the prompts against a metric.

WHY DSPY?
  Hand-tuning prompt strings is brittle and breaks when you swap models. DSPy turns
  prompting into OPTIMIZATION:
    - Signature  = declarative contract (inputs -> outputs + task description)
    - Module     = strategy over a signature (Predict, ChainOfThought, ReAct)
    - Optimizer  = algorithm (BootstrapFewShot, MIPROv2) that tunes the actual prompts
                   and few-shot examples to maximize YOUR metric.
  Result: reproducible, model-portable pipelines. Change the model -> recompile,
  don't rewrite prompts by hand.

Run:
  export OPENAI_API_KEY=sk-...
  python dspy_pipeline.py
"""

import dspy


# 0) Configure the language model DSPy will program against.
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))


# 1) A Signature = the CONTRACT. The docstring is the task description; fields declare
#    inputs and outputs. WHY: you say WHAT you want, not HOW to phrase the prompt.
class ClassifySentiment(dspy.Signature):
    """Classify the sentiment of a product review as positive, negative, or neutral."""

    review: str = dspy.InputField()
    sentiment: str = dspy.OutputField(desc="one of: positive, negative, neutral")


# 2) A Module = the STRATEGY. ChainOfThought asks the model to reason before answering.
#    WHY: swapping Predict <-> ChainOfThought <-> ReAct changes behavior without you
#    rewriting any prompt text.
classifier = dspy.ChainOfThought(ClassifySentiment)


def run_uncompiled() -> None:
    """Use the program as-is (no optimization yet)."""
    out = classifier(review="The battery dies in an hour. Very disappointed.")
    print("Predicted sentiment:", out.sentiment)


# --- Optional: compile/optimize against a metric -----------------------------------
def run_compiled() -> None:
    """Optimize the prompts/few-shot demos with a metric + tiny trainset.

    WHY: the optimizer spends LLM calls at compile time to find instructions and
    examples that maximize accuracy — automated prompt engineering.
    """
    trainset = [
        dspy.Example(review="I love it, works perfectly!", sentiment="positive").with_inputs("review"),
        dspy.Example(review="Broke after one day.", sentiment="negative").with_inputs("review"),
        dspy.Example(review="It's fine, nothing special.", sentiment="neutral").with_inputs("review"),
    ]

    # Metric: did we predict the right label? (exact match, case-insensitive)
    def metric(example, pred, trace=None) -> bool:
        return example.sentiment.lower() == pred.sentiment.lower()

    # BootstrapFewShot is a good starting optimizer for tiny datasets.
    # (For larger sets, MIPROv2 jointly optimizes instructions + demonstrations.)
    optimizer = dspy.BootstrapFewShot(metric=metric)
    compiled = optimizer.compile(classifier, trainset=trainset)

    out = compiled(review="Honestly the best purchase I've made this year.")
    print("Compiled prediction:", out.sentiment)


if __name__ == "__main__":
    run_uncompiled()
    # run_compiled()  # uncomment to run optimization (costs extra LLM calls)
