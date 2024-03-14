# RESTRuler: Evaluation Artifacts
> All artifacts related to the empirical evaluation of the [RESTRuler CLI](https://github.com/restful-ma/rest-ruler), a Java-based tool to identify design rule violations in OpenAPI descriptions (Java version >= 18 needed)

## Goal and Methods

The evaluation was concerned with three things:

- [Robustness](./01-robustness/): successful analysis runs for real world API descriptions
- [Performance efficiency](./02-performance/): analysis duration plus CPU and memory usage
- [Effectiveness](./03-effectiveness/): accurate identification of rule violations

For robustness and performance efficiency, we downloaded ~2.3k OpenAPI descriptions from https://apis.guru, a public repository of OpenAPI descriptions, and let RESTRuler analyze them.
For effectiveness, we performed a separate analysis of precision , i.e., how many false
positives, and recall, i.e., how many false negatives.

- Precision: random selection of reported violations from the `apis.gurus` benchmark per implemented rule with manual analysis (are the reported violations correct?)
- Recall: creation of a labeled gold standard together with 7 external experts (are the created violations reported?)

## Comments

- The used data set of OpenAPI descriptions is provided as a ZIP archive: `apis-json.zip`
- If you want to run or adapt the scripts:
  - Don't forget to install the required dependencies: `pip install -r requirements.txt`
  - You may have to change several paths in the scripts, e.g., your local path to `rest-ruler.jar`