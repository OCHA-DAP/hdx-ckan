PII FIELDS
==========

POSSIBLE ACTIONS RELATED TO PII
-------------------------------
#. *Echo* - scripts that run on AWS and scan uploaded resources for PII. The results are pushed back to CKAN

   * sets the **pii_report_flag** field to *"OK"*, *"FINDINGS"*, *"EXCEPTION"*
   * sets the **pii_report_id** field to the log path of the log file
   * sets the **pii_timestamp** field to current time in ISO without Z (without timezone) 
   * sets the **pii_predict_score** field to the calculated score 
#. *Resource Creation* - when creating a resource from the UI the maintainer can specify whether the resource contains PII. 
   If the user checks the checkbox then the dataset cannot be saved. Otherwise, if the checkbox is left unchecked, the **pii** field is set to the value *"false"*
#. *QA Dashboad* 

   #. *Run PII Check* (resource level, in the menu) - runs the *Echo* scripts
   #. *Confirm Risk Classification* (resource level, there is a "Confirm" link) - sets the **pii_is_sensitive** field
   #. *Confirm Not Sensitive* (dataset level, in the menu) - sets the **pii_is_sensitive** fields to *false* all resources in the dataset


DATASET PII FIELDS
------------------

#. **pii** - manually set by *Resource creation* UI (set from js)
#. **pii_report_flag** - set by *Echo*
#. **pii_report_id** - set by *Echo*
#. **pii_timestamp** - set by *Echo*
#. **pii_predict_score** - set by *Echo*
#. **pii_is_sensitive** - manually set by *QA Dashboard* / *Confirm Risk Classification* OR by *QA Dashboard* / *Confirm Not Sensitive*
