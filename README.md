Python 3 port of Tagged Message Delivery Agent (TMDA)
by Jonathan Kamens <<jik@kamens.us>>.

I did this port in January 2023 starting with the last "official"
release of TMDA by the original maintainer, version 1.1.2. I didn't
realize that there were two other post-1.1.2 forks,
[Kevin Goodsell's][kevin] and [Cédric Dufour's][cedric], and that the
latter port already has most of the work to port to Python 3. I should
have checked before doing my port; it would have saved me a lot of
work!

Having said that, at least for the time being I'm going to stick with
my version since it's working for me. I'm sharing it here on the off
chance that it might be useful for others. This version, or at least
the parts of it that I'm actually working, seems to be working fine
with Python 3.9.

See the README file for more information about what TMDA is. The Wiki
referenced there is broken, but you can access it
[through the Wayback Machine][wiki] if you'd like. The
[SourceForge tmda-users mailing list][sf] also still works.

For the most part the only changes I've made to the code are what was
necessary to get it to run and work under Python 3. However, there is
one significant new contribution I've made: a simple TMDA CGI wrapper
which allows you to whitelist and blacklist senders or delete messages
through a web server running on the same host as TMDA. See
`simple-tmda.cgi` in the `contrib` directory. It has a detailed
comment at the top explaining how to use it.

[kevin]: https://github.com/KevinGoodsell/tmda-fork
[cedric]: https://github.com/cedric-dufour/tmda
[wiki]: https://web.archive.org/web/20081026052520/http://wiki.tmda.net/
[sf]: https://sourceforge.net/p/tmda/mailman/
