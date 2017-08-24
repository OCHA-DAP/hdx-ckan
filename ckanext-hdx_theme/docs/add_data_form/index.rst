ADD DATA FORM
=============

Expected Update Frequency
-------------------------

The value of the field is usually the number of days after which a dataset is expected to be updated.
The exceptions to this are:

* *adhoc* has value -2
* *never* has value -1 ( initially the value 0 was used for this but it was decided that 0 is more suitable for *live*)
   The following patch was used for updating the database:
    `update package_extra set value='-1' where key='data_update_frequency' and value='0' and state='active';`
* *live* has value 0