jentool
-------

`jentool` is a command line tool for doing basic Jenkins maintenance tasks.

Installation
============

Into a `virtualenv`::

  virtualenv venv
  source venv/bin/activate
  pip install -e .
  # now you can use the tool
  jentoo -h


Configuration
=============

To configure `jentool`, a .ini style configuration file is needed::

     $ cat ~/.config/jentool.ini 
     [profile1]
     url=https://my-jenkins-instance
     user=joe
     password=123

     $ jentool -p profile1 nodes-list

Contributions
=============

Please use github (https://github.com/toabctl/jentool) issues
and pull requests for discussions and contribution.
