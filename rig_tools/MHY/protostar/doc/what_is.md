# What is Protostar?

## Introduction

Protostar is a DCC-agnostic procedural action framework. It is an
effective tool for modularizing and proceduralizing workflows in any
DCCs that come with a Python interface. Some of our inspirations are:
Block Party(ILM), Stitches(Blizzard), Houdini, and Unity.

**Design-guiding Mantras:**

+ **DCC-agnostic** - This is essential, as we don't want to build a modular
  system for a specific workflow in a specific DCC (e.g. rigging in Maya).
  Our goal is to make an independent system that any procedural workflows
  can be built upon.

+ **Easy to extend** - Empower each team with the ability to write and share
  their own actions with ease. A central library class should be in place to
  manage team-developed actions.

+ **Versatile, but not overwhelming** - We want to build a flexible system
  where action graphs can be formed in many ways. But when it comes to the
  user interface, it should still be presented as a straight-forward
  drag-n-drop node system. Advanced features, such as complex script override,
  should be accessible but not obvious.

## Key Concepts

+ **Action** - Action is the basic executable module in Protostar. Actions
  can be connected together via their parameters. Connected actions form an
  action graph.

+ **Action Graph** - A collection of actions, sub-graphs, and the connections
  between them. Executing an action graph will execute all objects within.
  Action graphs can be exported and imported via JSON.

+ **Action Library** - A factory class that acts as the entry point to all actions
  and graphs available to the user.

+ **Parameter** - Parameters are used to receive user inputs and pass data through
  a graph. Actions usually come with static(built-in) parameters. Users can also
  attach dynamic parameters to actions for storing and passing custom data.

## Dependencies

+ [Python](https://www.python.org) 2.7+
+ [mhy:python-core](https://git.woa.com/MHY/python-core)

## Getting Help

+ [The Getting Started](getting_started.html#getting-started) page has many usage
  examples on how to interact with the Action Library to search and
  instantiate actions.

  + Need info on a specific action? Check out the [Action
    Inspection](getting_started.html#get-action-details) section.

+ [The Developer Guide](developer_guide.html#developer-guide) covers everything you
  need to know about making actions and action graphs for your team.

+ [The Parameter Guide](parameter_guide.html#parameter-guide) contains detailed
  information on all the parameters supported by Protostar.

+ Take a look at the [FAQ section](faq.html#faq) to find answers to common problems.

## Roadmap

+ [TBD] Batch executing action graphs.
