

.. image:: https://circleci.com/gh/sematic-ai/sematic.svg?style=shield&circle-token=c8e0115ddccadc17b98ab293b32cad27026efb25
   :target: <LINK>
   :alt: CircleCI


Welcome to Sematic.

Sematic is an open-source development toolkit to help Data Scientists and Machine
Learning (ML) Engineers prototype and productionize ML pipelines in days not
weeks.

Find our docs at `docs.sematic.ai <https://docs.sematic.ai>`_.


.. image:: https://github.com/sematic-ai/sematic/raw/main/docs/images/Screenshot_README_1.png
   :target: https://github.com/sematic-ai/sematic/raw/main/docs/images/Screenshot_README_1.png
   :alt: UI Screenshot


Installation
------------

Instal Sematic with

.. code-block:: shell

   $ pip install sematic

Usage
-----

Start the app with

.. code-block:: shell

   $ sematic start

Then run an example pipeline with

.. code-block:: shell

   $ sematic run examples/mnist/pytorch

Create a new boilerplate project

.. code-block:: shell

   $ sematic new my_new_project

Or from an existing example:

.. code-block:: shell

   $ sematic new my_new_project --from examples/mnist/pytorch

Then run it with

.. code-block:: shell

   $ sematic run my_new_project.main

See our docs at `docs.sematic.ai <https://docs.sematic.ai>`_\ , and join us on `Discord <https://discord.gg/PFCpatvy>`_.

Contribute
----------

See our Contributor guide at `docs.sematic.ai <https://docs.sematic.ai>`_.
