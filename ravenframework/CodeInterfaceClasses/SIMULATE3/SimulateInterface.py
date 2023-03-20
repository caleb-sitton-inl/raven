# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on August 01, 2022
@author: khnguy22

comments: Interface for Simulate3 Simulation
"""
import os
from . import SpecificParser
from ...CodeInterfaceBaseClass import CodeInterfaceBase
from .SimulateData import SimulateData

class Simulate(CodeInterfaceBase):
  """
    Simulate Interface. Reading output from simulate then export to csv dat file.
  """
  def __init__(self):
    """
      Constructor
      @ In, None
      @ Out, None
    """
    CodeInterfaceBase.__init__(self)
    self.sequence = []   # this contains the sequence that needs to be run. [simulate]
    self.outputRoot = {} # the root of the output sequences

  def _readMoreXML(self,xmlNode):
    """
      Function to read the portion of the xml input that belongs to this specialized class and initialize
      some members based on inputs. This can be overloaded in specialize code interface in order to
      read specific flags
      @ In, xmlNode, xml.etree.ElementTree.Element, Xml element node
      @ Out, None.
    """
    CodeInterfaceBase._readMoreXML(self,xmlNode)
    sequence = xmlNode.find("sequence")
    if sequence is None:
      self.sequence = ['simulate'] #may be no need
    else:
      self.sequence = [elm.strip() for elm in sequence.text.split(",")]


  def findInps(self,inputFiles):
    """
      Locates the input files required by SIMULATE3 Interface
      @ In, inputFiles, list, list of Files objects
      @ Out, inputDict, dict, dictionary containing xml and a dummy input for SIMULATE3
    """
    inputDict = {}
    SimulateData = []
    SimulatePerturb = []
    SimulateInput = []
    for inputFile in inputFiles:
      if inputFile.getType().strip().lower() == "simulatedata":
        SimulateData.append(inputFile)
      elif inputFile.getType().strip().lower() == "input":
        SimulateInput.append(inputFile)
      else:
        SimulatePerturb.append(inputFile)
    if len(SimulatePerturb) > 1 or len(SimulateData) > 1 or len(SimulateInput) >1:
      raise IOError('multiple simulate data/perturbed input files have been found. Only one for each is allowed!')
    # Check if the input is available
    if len(SimulatePerturb) <1 or len(SimulateData) <1:
      raise IOError('simulatedata/perturb input file has not been found. Please recheck!')
    # add inputs
    inputDict['SimulateData'] = SimulateData
    inputDict['SimulatePerturb'] = SimulatePerturb
    inputDict['SimulateInput'] = SimulateInput
    return inputDict

  def generateCommand(self, inputFile, executable, clargs=None, fargs=None, preExec=None):
    """
      Generate a command to run Simulate using an input with sampled variables generated by specific parser.
      Commands are a list of tuples, indicating parallel/serial and the execution command to use.
      @ In, inputFile, string, input file name
      @ In, executable, string, executable name with absolute path (e.g. /home/path_to_executable/code.exe)
      @ In, clargs, dict, optional, dictionary containing the command-line flags the user can specify in the input
        (e.g. under the node < Code >< clargstype = 0 input0arg = 0 i0extension = 0 .inp0/ >< /Code >)
      @ In, fargs, dict, optional, a dictionary containing the axuiliary input file variables the user can specify
        in the input (e.g. under the node < Code >< fargstype = 0 input0arg = 0 aux0extension = 0 .aux0/ >< /Code >)
      @ In, preExec, string, optional, a string the command that needs to be pre-executed before the actual command here defined
      @ Out, returnCommand, tuple, tuple containing the generated command. returnCommand[0] is the command to run the
        code (string), returnCommand[1] is the name of the output root
    """
    inputDict = self.findInps(inputFile)
    sim3Input = str(inputDict['SimulateInput'][0]).split()[1]
    workingDir = os.path.dirname(sim3Input)
    sim3Input = sim3Input.replace(workingDir+'/','').strip() # can use getfilename() too

    executeCommand = []
    seq = self.sequence[0] # only one sequence value
    self.outputRoot[seq.lower()] = inputDict['SimulateInput'][0].getBase()
    executeCommand.append(('parallel',executable+' '+sim3Input))
    # returnCommand = executeCommand, list(self.outputRoot.values())[-1]
    returnCommand = [('parallel','echo')], list(self.outputRoot.values())[-1]
    return returnCommand

  def createNewInput(self, currentInputFiles, origInputFiles, samplerType, **Kwargs):
    """
      Generates new perturbed input files for Simulate (perturb xml file then generate inp)
      @ In, currentInputFiles, list,  list of current input files
      @ In, origInputFiles, list, list of the original input files
      @ In, samplerType, string, Sampler type (e.g. MonteCarlo, Adaptive, etc. see manual Samplers section)
      @ In, Kwargs, dict, dictionary of parameters. In this dictionary there is another dictionary called "SampledVars"
        where RAVEN stores the variables that got sampled (e.g. Kwargs['SampledVars'] => {'var1':10,'var2':40})
      @ Out, newInputFiles, list, list of new input files (modified or not)
    """
    # may be no need ?
    currentInputsToPerturb = [item for subList in self.findInps(currentInputFiles).values() for item in subList]
    originalInputs         = [item for subList in self.findInps(origInputFiles).values() for item in subList]

    perturbInput = str(self.findInps(currentInputFiles)['SimulatePerturb'][0]).split()[1]
    sim3Input = str(self.findInps(currentInputFiles)['SimulateInput'][0]).split()[1]
    sim3DataInput = str(self.findInps(currentInputFiles)['SimulateData'][0]).split()[1]
    workingDir = os.path.dirname(perturbInput)
    sim3Input = sim3Input.replace(workingDir+'/','').strip()
    perturbedVal = Kwargs['SampledVars']
    sim3Data = SpecificParser.DataParser(sim3DataInput)
    perturb = SpecificParser.PerturbedPaser(perturbInput, workingDir, sim3Input, perturbedVal)
    perturb.generateSim3Input(sim3Data)
    return currentInputFiles

  def checkForOutputFailure(self,output,workingDir):
    """
      This method is called by the RAVEN code at the end of each run  if the return code is == 0.
      This method needs to be implemented by the codes that, if the run fails, return a return code that is 0
      This can happen in those codes that record the failure of the job (e.g. not converged, etc.) as normal termination (returncode == 0)
      Check for FATAL error in SIMULATE3 output
      @ In, output, string, the Output name root
      @ In, workingDir, string, current working dir
      @ Out, failure, bool, True if the job is failed, False otherwise
    """
    failure = False
    badWords  = ['FATAL']
    outFile = os.path.join(workingDir,output+'.out')
    if os.path.exists(outFile):
      outputToRead = open(outFile, "r")
      readLines = outputToRead.readlines()
      outputToRead.close()
      for badMsg in badWords:
        if any(badMsg in x for x in readLines[-20:]):
          failure = True
    return failure

  def finalizeCodeOutput(self, command, output, workingDir):
    """
      This method converts the Sim3 outputs into a RAVEN compatible CSV file
      @ In, command, string, the command used to run the just ended job
      @ In, output, string, the Output name root
      @ In, workingDir, string, current working dir
      @ Out, output, string, output csv file containing the variables of interest specified in the input
    """
    filesIn = {}
    for key in self.outputRoot.keys():
      if self.outputRoot[key] is not None:
        filesIn[key] = os.path.join(workingDir,self.outputRoot[key]+'.out')
        outputParser = SimulateData(filesIn[key])
        outputParser.writeCSV(os.path.join(workingDir,output+".csv"))






