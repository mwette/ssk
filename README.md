# ssk

simple statechart kit : convert MagicDraw StateMachines to C code

This package is a set of python scripts that will read a MagicDraw
file (.mdzip), extract a StateMachine definition and generate an
implementation.  So far we are working on a generating C code.

The code is covered by the GNU Lesser Public License V3.
See the file COPYING in the distribution.

# files

This is a lit of the files and what they do.

## uanlyz.py 

analysis of UML StateMachine - adds more info to tree
 1. add index for each state in a container
 2. for each composite state, add number of bits needed to encode
    this composite state (shallow and/or deep?)
 3. for each composite state, add number of bytes needed to encode
    this composite state (shallow and/or deep?)
 4. for each composite state, add max number of concurrent regions

## ssk1.py 
* class StateChart
* class State
* class Region
* class Transition
* used_ids(mach) : return list of reserved ids for mach
* assign_leaf_ids(mach, reserved) : assign Ids, leaves first
* assign_node_ids(mach, reserved) : assign Ids, leaves first
* gen_idmap(mach) : set up map of id to state
* assign_nslots(mach) : ???
* assign_offsets(mach) : ???
* expand_nslots(mach) : nslot for region of to fill out max space needed
* index_ssk(mach): add depth to SSK regions/states
+ elab_state(mach, state) : elaborate state?
+ merge_encsts(est0, ests) : xxx
+ merge_states(mach, est0, states) :
+ merge_pstate(est0, pstate) :
+ find_transitions(mach, label) :
+ mach_labels(mach) : find all labels used in a machine
+ state_depth(mach, encst) : return lowest state depth
+ raise_depth(mach, est0) : raise depth of est0 one level
+ buildit(mach) : ???

## uml2ssk.py 

class UMLtranslator
* def reset
* def set_model
* def find_stm
* def find_all_stms
* def translate_stm

`uml_to_ssk(model, machname)` : given UML model return (ssk, diag|None)

## mdreader 

reads mdzip file and extracts statemachines

## mdcnvt 

driver
* read mdzip file
* optionally call uanlyz.ModelValidator().validate_model
* call uml_to_ssk(model, machname) => ss
* call ssk1.index_ssk(ss)
* call sskP.SskXmlWriter().write()
* maybe dump .c file: M2Impl(ss).dump_body()
* maybe dump .pml file: M2Impl(ss).dump_body()
