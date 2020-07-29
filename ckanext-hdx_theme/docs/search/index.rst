INFORMATION ABOUT THE SEARCH ENGINE IN HDX
==========================================

The search engine in HDX / CKAN is based on `Apache Solr <https://lucene.apache.org/solr/>`_

By default the search queries in HDX are processed by using
`the DisMax Query Parser <https://lucene.apache.org/solr/guide/6_6/the-dismax-query-parser.html>`_


Field types
-----------
There are 2 types of fields that we are searching through:

*  **string** - These fields are not split into terms when indexed in solr. So a query term must match them exactly in order for
   solr to be able to find the term in a 'string' field.
   See the *name* field below as an example for that.
*  **text** - These fields are split into terms and stemmed before being indexed.
   Ex: 'population affected' would be indexed as 'popul' and 'affect'
   So a query term of "populated" would match the above example.


Field list
----------
The list of dataset fields that are used for searching in descending order of their importance (weight):

*  **name** (string) - this is the string that appears at the end of the URL, as in */dataset/dataset-name*.
   Please note that in order to match this field an exact match needs to exist in the query.
*  **title** (text) - this is the title of a dataset
*  **vocab_text_Topics** (text) - these are the new vocabulary tags of a dataset. They used to be of type *string* in default CKAN.
   We switched them to text.
*  **groups** (string) - these are the ISO3 codes of the locations that a dataset is linked to
*  **notes** (text) - this is the description of a dataset
*  **text** (text) - NOTE: not to be confused with the "text" type.
   This is a "catch-all" field that contains all the text from almost all the fields of a dataset bundled together.
   Example of text that is stored in the text field: resources information, license information, all the fields mentioned above, etc

Relevance scoring
-----------------
A query is split into terms and then each term is searched for in the list of fields mentioned above.
So, for a document, each term-field pair gets a score. For a term, the maximum score is the most important one.
The rest of the scores are added to the final score for that term with a 0.3 coefficient.
The total score for a document is the sum of the scores for each term.

Example - for query "conflict data" and dataset A:

*  title - conflict score is 20 and notes - conflict score is 6. Then the total score for dataset A with therm 'conflict' is 20 + 0.3 * 6 = 21.8
*  title - data score is 10 and notes - data score is 5, text - data score is 2 . Then the total score for dataset A with therm 'conflict' is 10 + 0.3 * 7 = 12.1
So the total score for document A is 33.9

Please note that there is also a *small* score boost given to datasets that have more page views in the last 14 days.

Number of terms that must match
-------------------------------
*  if a term in a query starts with a '+', then all documents in the search result **must** contain it
*  if a term in a query starts with a '-', then **none** of the documents in the search result can contain it
*  the other terms are optional, with the following rules:
    *  if there are up to 2 terms, they all need to match
    *  3 to 5 terms, all except one need to match ( for example, if the query is "health news data", any document in the result list needs to have at least 2 of the terms)
    *  for 6 terms or above, a document must contain at least 80% of the terms

