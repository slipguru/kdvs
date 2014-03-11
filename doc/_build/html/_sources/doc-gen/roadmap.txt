.. _roadmap:

Roadmap
*******

This section lists possible improvements and new features. The points are specified
in no particular order.

Codebase
--------

* Refactor existing 'experiment.py' application

    * extract walking of 'category tree' into API component
    * extract 'operations map' construction (binary/textual) and walking into API component
    * extract job production and submission ('submitSubsetOperations') into API component
    * extract retrieving raw job results into API component
    * make group completion an API friendly concept, reimplement and separate from application
    * extract job postprocessing into API component
    * extract selections into API component
    * make plots storage configurable
    * make these mappings reimplemented as API components:

        * subsets
        * pkcid2ssname
        * technique2DOF
        * submission_order

    * make selectors marking uniformly pkcs/variables with selection constants;
      make inner selectors more API friendly

    * decouple selectors from techniques (likely requires revision of Technique/Results
      abstract classes)

    * streamline report implementation and decouple it from application as much as
      possible (additional_data!)

    * extract command line parameters from application initialization and make it
      as declarative as possible

    * refactor configuration of static data files into something more descriptive
      and decouple it from application

    * separate textual serialization from binary serialization and make it configurable
      from command line

* Reimplement component initializers as API concept

* Rewrite 'experiment.py' application as the general application that interprets
  application profile (HGNC may be a problem here!)

* Make generator of configuration file for non-power users that utilizes GUI
  or change configuration file content into something more declarative (XML?)

* Optimize memory consumption of 'experiment.py' application as much as possible
  (Results instances may be a problem here!)

Testing
-------

* Unit tests

    * report/L1L2
    * envop/L1L2 (create mock RLS like technique) (to be finished after operations map has API)

* Function tests on synthetic data

* System tests

