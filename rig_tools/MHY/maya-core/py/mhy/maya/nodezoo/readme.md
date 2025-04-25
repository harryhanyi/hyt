# Nodezoo

Nodezoo is an in-house maya node api library. It provides interface for all maya nodes and also some plugin nodes studio maintains internally.   

# What is it for?

1. Nodezoo is an object-oriented high level factory interface based on
maya built-in python api and cmds. It is more intuitive to learn 
because the functionality of an object is directly associated with
 the object itself.

2. Nodezoo centralizes all the node classes and functions and shared with other
 front end tools. Its goal is to minimize duplicated implementations. 

3. Nodezoo provides easy methods to query, edit, export or import 
nested attributes which is cumbersome using native maya api.

# Core features

1. object oriented
2. factory paradigm
3. customized node
4. serializable

 
# Detailed Documentation

+ [Node](doc/node.md)
+ [Attribute](doc/attribute.md)
 
# Limitation
Since nodezoo created another layer of logic on top of the maya
native api, so user may comes to a bottleneck if they need to
push the performance to some level. So it might not be suitable for
applications involving large number of nodes or attributes editing
and with very high-performace requirements.







