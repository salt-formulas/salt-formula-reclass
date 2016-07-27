# -*- coding: utf-8 -*-
'''
Management of reclass metadata
==============================

.. code-block:: yaml

    node01:
      reclass.node_present:
      - name: hostaname.domain.com
      - path: _generated
      - cluster: default
      - environment: prd
      - classes:
        - neco.service.neco
        - neco2.class.neco.dal
      - parameters:
          neco: value1
          neco2: value2

'''


def __virtual__():
    '''
    Always present
    '''
    return 'reclass'

