A small set of useful utilities for working with WSGI web apps.

wiseguy.webtest is a fork of Olly Cope's Flea library, with parts
rewritten to work with Werkzeug instead of Pesto, to be more
backwards compatible with Ian Bicking's WebTest, and to more suit a
style where your tests are also definitions of your apps behaviour.

wiseguy.utils is an attempt to start reducing some duplication across
my web projects by factoring out similar pieces into this project.
(And coincidentally also contains contributions from Olly Cope).

It is certainly not yet intended to be ready for other peoples use,
though you are welcome to try.
