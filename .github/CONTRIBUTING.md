# Contributing

## Style Guidelines

Please stay conform to PEP8.  The only thing not so important is the
line length, but trying too keep it <90 chars is good practise.

## Testing

You should _always_ test your code before you commit – at the very
least before you decide to make a PR.

Also, if you introduce new code, include at least some basic tests.
Falling behind in coverage because of laziness is bad, really bad.

Similar for bugs: When fixing a bug, introduce a test case for it –
and verify it fails before the fix has been introduced.  You might
want to use the
[@expectedFailure](https://docs.python.org/3.5/library/unittest.html#unittest.expectedFailure)
decorator and create a separate commit introducing the test before the
fix – but these details are not so important.


## Pushing

Don't push to develop directly, _always_ create a PR!  Only then the
CI can verify your code.
