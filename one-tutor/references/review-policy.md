# Review and mastery policy

The bundled CLI uses a transparent SM-2-inspired schedule. Keep the policy understandable to the learner; it is a prioritization aid, not a claim about cognition.

## Selection buckets

Read the mix from `config.json`:

```json
{
  "mix": {
    "new": 0.5,
    "review": 0.35,
    "weak": 0.15
  }
}
```

- `new`: active, independent questions with no prior attempt or exclusion record.
- `review`: previously graded questions whose `next_review` is due, plus repaired questions that were previously excluded and then reactivated.
- `weak`: unmastered questions from topics accumulating errors or low-confidence successes.
- `fill`: safe fallback when one requested bucket lacks enough questions.

Adjust proportions to the learner's phase. Use more new questions during coverage, more review near consolidation, and more weak-topic questions after diagnostic tests.

When due review items exist, even a one-question session reserves a review slot. Inside that slot, high-confidence incorrect answers come first, followed by other incorrect answers and then uncertain correct answers. Weak-topic selection preserves topic severity order while randomizing questions only within the same topic.

## Confidence interpretation

- `high` / `稳`: retrieve confidently.
- `medium` / `不确定`: answer with meaningful doubt.
- `low` / `蒙`: guess or retrieve with little confidence.

Treat confidence as evidence separate from correctness:

- High-confidence incorrect: likely misconception; review first.
- Low-confidence correct: possible lucky guess; schedule soon.
- Medium-confidence correct: reinforce rather than mark mastered.
- High-confidence repeated correct: gradually lengthen the interval.

## Scheduling behavior

- Reset an incorrect item to a one-day interval and reduce its ease.
- Start correct items at one day, then three days.
- Multiply later intervals by the item's ease.
- Cap low-confidence correct answers at two days.
- Cap medium-confidence correct answers at seven days.
- Mark an item mastered only after at least three successful repetitions and an interval of at least seven days.

Do not equate “mastered” with permanent knowledge. A mastered item remains eligible when its review date arrives.

## Error categories

Use these defaults and replace them with a more precise diagnosis when evidence supports it:

- `misconception`: confident but incorrect conceptual model.
- `knowledge-gap`: incorrect with uncertainty or guessing.
- `lucky-guess`: correct with low confidence.
- `uncertain-correct`: correct with medium confidence.
- `invalid-question`: broken, ambiguous, incomplete, or unreliable item.

Add domain-specific categories only when they drive a different intervention, such as `calculation-slip`, `misread-negation`, `terminology-confusion`, or `procedure-order`.

## Changing the algorithm

Preserve the history schema and make scheduling changes explicit. Test changes with a small synthetic project before applying them to a learner's live history. Never silently rewrite prior attempts.
