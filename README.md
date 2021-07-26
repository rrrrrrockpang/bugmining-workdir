# bugmining-workdir
This is the (temporary) Git repo that holds the bug-mining working directories.

Eyeball the failing tests:

For each entry in rev pairs:
    check if the bug id exist in trigger test
    if no:
        determine the revision hash of the fixed version from active-bugs.csv
        look up failing test of the revision hash
        run mvn test
        
        check whether the errors are consistent / the number is different

flagging for manual inspection.


1. bug 3 couldn't compile `mvn test`
2. bug 42, 48 appears to just change comments
3. Not sure why bug 43, 48 is not here
4. All other bugs are consistent