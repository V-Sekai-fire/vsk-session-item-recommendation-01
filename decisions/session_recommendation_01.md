We’ll perform this set of operations for each [query item, ground truth item] pair in our test set, to compute an overall score using Recall@K and MRR@K.

Context window 13 and 26.

ModernBERT

Recommendations are typically based on the most recent interaction by the user, called the query item. In this case, we’ll treat the last item (“cap” in our highlighted set of items below) as the query item, and use that to generate a set of recommendations.

The item outside of the highlighted box (in this case, a “water bottle”) will be the ground truth item, and we’ll then check whether this item is contained within our generated recommendations.

Remove sessions that contain fewer than three purchased items.

A session with only two, for instance, is just a [query item, ground truth item] pair and does not give us any examples for training.

The user’s actual next selection (the final item in the user’s sequence) is considered the ground truth item, and we check whether that item is found in our list of generated recommendations.

---

date: the date of the action

user: identifier of the user

item: identifier of the item

action: type of action that the user performed on the item

#1 Design a candidate retriever to identify the most relevant items for a user (based on user and item characteristics) minus the items that the user can no longer interact with.

#2 Rank the candidates (based on user and item information).

recid: ID of the recommendations produced.

recommendations: A list of dictionaries, each defined by an id key with the ID of the entity recommended.

source: Details on the source of the recommendations, which could include a eneral explanation of the recommendations, the update date, etc.

https://www.the-odd-dataguy.com/2024/04/07/features-principles-recsys/

```
get recommendations
    pipelineid: Identifier for the project/pipeline associated with the recommendations.
    userid: Identifier defining a user.
    itemid (optional): Identifier of an item used as context for related items features.
    k (optional): Number of items to include in the recommendations.
        default=20
        min=1
        max=100
    retriever strategy (optional): Name of the retriever phase, linked to the pipelineid.
        default=default
    ranker strategy (optional): Name for the ranker phase, linked to the pipelineid.
        default=default
    exploration factor (optional): Factor of exploration in the pipeline.
        default=0.1
        min=0
        max=1
    promoted items (optional): List of items to be promoted in the recommendations.
    excluded items (optional): List of items to be excluded in the recommendations.
    detailed output (optional): Boolean to determine if additional details (metadata, explanation, score, etc.) should be included in the list of recommended items.
        default=False

get trends
    Inputs such as pipelineid, userid, itemid, k, promoted items, excluded items, and detailed output are included in this route as well.
    time period: Time period in seconds to determine the trends.
        default = 604800 seconds (7 days)
        min = 3600 seconds (1 hour)
        max = 1209600 seconds (14 days)

get random recommendations
```

These inputs allow for a tailored recommendation experience, where the integrator can tweak the output easily and enabling users to receive personalized, trending, or random item suggestions based on their preferences and context.

https://github.com/sb-ai-lab/RePlay

Hierarchical contextual bandit on MovieLens dataset
