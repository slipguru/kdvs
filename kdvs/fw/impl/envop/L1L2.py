# Knowledge Driven Variable Selection (KDVS)
# Copyright (C) 2014 KDVS Developers. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

r"""
Provides concrete functionality for environment--wide operations (envops) related
to statistical techniques using `l1l2py <http://slipguru.disi.unige.it/Software/L1L2Py/>`_ library.
"""

from kdvs.core.dep import verifyDepModule
from kdvs.core.error import Error
from kdvs.core.util import pairwise
from kdvs.fw.EnvOp import EnvOp
import l1l2py

class L1L2_UniformExtSplitProvider(EnvOp):
    r"""
The parametrizable pre--EnvOp (i.e. that will be executed before all computational jobs
from statistical techniques for current category) that generates splits from
given labels vector, and places the result directly into specific placeholder
variable that the statistical technique exposes. This way, any interested
statistical technique may share exactly the same split. This approach is used in
:class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2` and :class:`~kdvs.fw.impl.stat.L1L2.L1L2_RLS`
techniques so that they can share one uniform external split. To use it, the
instance of this class must be configured with the following parameters:

    * 'enclosingCategorizerID' -- the identifier of the :class:`~kdvs.fw.Categorizer.Categorizer` on the level this EnvOp will be called
    * 'extSplitParamName' -- name of the parameter that holds the number of splits to be made ('the counter')
    * 'extSplitPlaceholderParam' -- name of the parameter in statistical technique that will hold the generated split

For instance, if 'extSplitPlaceholderParam' equals to 'splits', then such parameter
must be present during configuration of statistical technique, with initial value
None, in configuration file:

    * techConf1 = {..., 'splits' : None, ...}

This EnvOp works assuming the following conditions are met:

    * (1) in all statistical techniques that expose placeholder parameter, the 'counter' value is exactly the same
    * (2) in all categories on current hierarchy level, all data subsets have the same single statistical technique assigned for processing (so we obtain single 'counter' value),
    * (3) there is at least one valid categorizer BELOW the enclosing one with at least one technique that exposes placeholder parameter.

If any of those conditions is NOT met, an Error is raised.
    """
    version = '1.0.5'
    uesp_parameters = ('enclosingCategorizerID', 'extSplitParamName', 'extSplitPlaceholderParam')

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones; the parameters are: 'enclosingCategorizerID',
    'extSplitParamName', 'extSplitPlaceholderParam'

Raises
------
Error
    if specific version of 'l1l2py' library is not present
        """
        verifyDepModule('l1l2py')
        if self._verify_version():
            super(L1L2_UniformExtSplitProvider, self).__init__(self.uesp_parameters, **kwargs)
        else:
            raise Error('L1L2Py version "%s" must be provided to use this class!' % self.version)

    def _verify_version(self):
        return l1l2py.__version__ == self.version

    def perform(self, env):
        r"""
Perform generation of splits and put them into all statistical techniques
that expose certain placeholder parameter. Refer to the comments for the detailed
procedure.

Parameters
----------
env : :class:`~kdvs.core.env.ExecutionEnvironment`
    concrete instance of ExecutionEnvironment that will be modified in--place

Raises
------
Error
    if the enclosing categorizer was not found
Error
    in the cases explained above
        """
        # here we perform single call to determine indexes of 'external splits'
        # used by L1L2 and RLS techniques implemented in l1l2py package

        # we will look for this parameter across all probed techniques
        extSplitParamName = self.parameters['extSplitParamName']
        # we will store external splits data in this placeholder parameter in
        # all probed techniques
        extSplitPlaceholderParam = self.parameters['extSplitPlaceholderParam']

        # first we obtain labels directly from the environment
        labels = env.var('labels_num')

        # next we need to obtain actual number of external splits to create;
        # this requires access to all instances of statistical techniques that harbor
        # 'extSplitParamName' parameter

        # in order to do so we need to:
        # 1. access operation map
        # 2. access categorizer immediately below us in the chain
        # 3. take all of its categories
        # 4. access all instances of associated statistical techniques
        # 5. check if they use 'extSplitParamName' parameter
        # 6. if so, check if value of this parameter is the same for all of them

        # 1. ---- access operation map
        operations_map = env.var('operations_map')

        # 2. ---- access categorizer immediately below us in the chain
        enclosingCategorizerID = self.parameters['enclosingCategorizerID']
        # access categorizers chain
        profile = env.var('profile')
        cchain = profile['subset_hierarchy_categorizers_chain']
        # we need to identify next immediate categorizer in the chain
        # to do this we split categorizer chain in pairs
        nextCategorizerID = None
        for currentID, nextID in pairwise(iter(cchain)):
            if currentID == enclosingCategorizerID:
                # next found finish looping
                nextCategorizerID = nextID
                break
        # if current categorizer was LAST in chain, we obviously cannot find the
        # next one; we raise warning and finish now
        if nextCategorizerID is None:
            raise Error('Next immediate categorizer of %s in the chain was not found! (Check if there are categorizers below)' % enclosingCategorizerID)
            return

        # 3. ---- take all of its categories
        categorizers = env.var('pc_categorizers')
        enclosingCategorizer = categorizers[nextCategorizerID]
        categories = [enclosingCategorizer.uniquifyCategory(c) for c in enclosingCategorizer.categories()]

        # 4. ---- access all instances of associated statistical techniques
        # here we will store all encountered parameter values
        external_ks = set()
        techs = dict()
        # walk categories
        for category in categories:
            copmap = operations_map[category]
            # get all PKCs associated with technique
            csymbols = [s for s in copmap.keys() if not s.startswith('__') and not s.endswith('__')]
            # make sure we get unique IDs
            assert len(csymbols) == len(set(csymbols))
            ctech = set()
            for csymbol in csymbols:
                ctechnique = copmap[csymbol]['__technique__']
                ctech.add(ctechnique)
            # we can still encounter distinct techniques in operations map
            # (due to data structures corruption); in that case report it and finish now
            if len(ctech) != 1:
                raise Error('Unique category was not determined across PKCs for category %s! (found %d)' % (category, len(ctech)))
                return
            # get instance from the first associated PKC
            ctechnique = copmap[csymbols[0]]['__technique__']
            techs[category] = ctechnique
            # 5. ---- check if they use 'external_k' parameter
            try:
                category_external_k = ctechnique.parameters[extSplitParamName]
            except KeyError:
                raise Error('Technique %s has no associated parameter %s!' % (ctechnique.__class__, extSplitParamName))
                return
            # we will determine later if values are unique across all categories
            external_ks.add(category_external_k)
        # 6. ---- if so, check if value of this parameter is the same for all of them
        if len(external_ks) != 1:
            raise Error('Unique value of parameter %s was not determined across categories! (found %d)' % (extSplitParamName, len(external_ks)))
            return

        # we accessed parameter we were looking for and all looks good so far
        external_k = next(iter(external_ks))

        # now we perform call that produces external splits that may be used across
        # categories below if they are interested
        ext_split_sets = l1l2py.tools.stratified_kfold_splits(labels, external_k)

        # store external splits data directly in the instance of each technique involved
        for tech in techs.values():
            tech.parameters[extSplitPlaceholderParam] = ext_split_sets
