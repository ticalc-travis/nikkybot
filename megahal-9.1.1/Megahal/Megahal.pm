package Megahal;

use 5.008;
use strict;
use warnings;
use Carp;

require Exporter;
use AutoLoader;

our @ISA = qw(Exporter);

# Items to export into callers namespace by default. Note: do not export
# names by default without a very good reason. Use EXPORT_OK instead.
# Do not simply export all your public functions/methods/constants.

# This allows declaration	use Megahal ':all';
# If you do not need this, moving things directly into @EXPORT or @EXPORT_OK
# will save memory.
our %EXPORT_TAGS = ( 'all' => [ qw(
	MEGAHAL_H
) ] );

our @EXPORT_OK = ( @{ $EXPORT_TAGS{'all'} } );

our @EXPORT = qw(
	MEGAHAL_H
);

our $VERSION = '0.01';

sub AUTOLOAD {
    # This AUTOLOAD is used to 'autoload' constants from the constant()
    # XS function.

    my $constname;
    our $AUTOLOAD;
    ($constname = $AUTOLOAD) =~ s/.*:://;
    croak "&Megahal::constant not defined" if $constname eq 'constant';
    my ($error, $val) = constant($constname);
    if ($error) { croak $error; }
    {
	no strict 'refs';
	# Fixed between 5.005_53 and 5.005_61
#XXX	if ($] >= 5.00561) {
#XXX	    *$AUTOLOAD = sub () { $val };
#XXX	}
#XXX	else {
	    *$AUTOLOAD = sub { $val };
#XXX	}
    }
    goto &$AUTOLOAD;
}

require XSLoader;
XSLoader::load('Megahal', $VERSION);

# Preloaded methods go here.

# Autoload methods go after =cut, and are processed by the autosplit program.

1;
__END__
# Below is stub documentation for your module. You'd better edit it!

=head1 NAME

Megahal - Perl extension for the Megahal conversation simulator library.

=head1 SYNOPSIS

  use Megahal;

  Megahal::megahal_initialize();
  Megahal::megahal_do_reply(texte, log);
  Megahal::megahal_learn_no_reply(texte, log);
  Megahal::megahal_cleanup();

=head1 ABSTRACT

  Megahal is a conversation simulator that learns as you talk to it.
  It uses a Markov Model to learn how to hold a conversation. It is
  possible to teach Meagahal to talk about new topics, and in
  different languages.

=head1 DESCRIPTION

=over

=item megahal_initialize()

Initialize megahal brain. Required before other functions are called.

=item megahal_do_reply(text, log)

Update the brain by feeding him the input B<text>. Logging is controlled via
the B<log> boolean. Returns the answer of the bot.

=item megahal_learn_no_reply()

Same as above but without making a reply. Much faster and typically used in
scripts for quick learning.

=item megahal_cleanup()

You need to call this function to save the brain, and finish Megahal.

=back

=head1 FILES

Megahal looks for the following files in the current directory:

=over

=item megahal.brn

Megahal brain.

=item megahal.ban

List of words which cannot be used as keywords.

=item megahal.log

Log file for errors.

=item megahal.txt

Log file for the conversation.

=item megahal.swp

Keyword translation for Megahal. If Megahal choose "why" as keyword and find a
line containing "why because" in a line of this file then "why" gets translated
in "because" in the reply.

=head1 SEE ALSO

http://megahal.sourceforge.net/

=head1 AUTHOR

This page was written by Laurent Fousse, E<lt>laurent@komite.netE<gt>.

=head1 COPYRIGHT AND LICENSE

Copyright 2003 by Jason Hutchens, David N. Welton and others.

This library is free software; you can redistribute it and/or modify
it under the GNU General Public Licence.

=cut
