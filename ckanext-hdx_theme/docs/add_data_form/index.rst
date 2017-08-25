ADD DATA FORM
=============

Expected Update Frequency
-------------------------

The value of the field is usually the number of days after which a dataset is expected to be updated.
The exceptions to this are:

* *adhoc* has value -2
* *never* has value -1 ( initially the value 0 was used for this but it was decided that 0 is more suitable for *live*)
   The following patch was used for updating the database:
    :code:`update package_extra set value='-1' where key='data_update_frequency' and value='0' and state='active';`
* *live* has value 0

If a sysadmin sets the value to *Live*, *Adhoc* or *Never* then a normal user will see that value in the
drop down (even if he normally wouldn't see it). Otherwise there would be a problem when a normal user would save the
dataset form because the frequency field would get reset .

If a normal user decides to change that field from Never to Every day then the Never value will no longer appear
in the dropdown next time the user accesses the dataset form.