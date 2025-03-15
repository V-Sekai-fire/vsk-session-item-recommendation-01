
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