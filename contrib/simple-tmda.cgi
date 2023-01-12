#!/usr/bin/env perl

# This script is a simple CGI front end to TMDA, the Tagged Message
# Delivery Agent. You can whitelist sender, blacklist senders, and
# delete messages through the user interface this script provides.
# It's password-authenticated and stores a persistent cookie in your
# browser so you don't have to log in repeatedly.
#
# To use it you need the following on the server TMDA is installed on:
#
# * Perl
# * All the Perl modules listed below
# * A web server
# * The ability to configure the web server to run the script as you,
#   e.g. by putting it in your public_html directory if you're using
#   Apache httpd
# * tmda-pending present in the script's search path when the web
#   server invokes it
#
# Once you've set up all of the above, run the script as yourself with
# the single argument "init" and it'll initialize the cookie
# encryption. You don't actually NEED to do this, since if there's no
# cookie encryption key configured it'll create it automatically the
# first time it's run from the web, but it doesn't hurt to do it in
# advance.
#
# Then run the script with the single argument "add-password" and
# it'll prompt for a username and password to configure. The username
# has no relationship to your UNIX username or to who the script runs
# as; that's controlled by the web server. The username and password
# are just for authenticating to the script. You can add multiple
# usernames and passwords if you want, but that won't log you in as
# different UNIX users. For that you need to put the script in
# multiple user's public_html directories (or whatever).
#
# The cookie encryption key is stored in ~/.tmda_key and the passwords
# are stored in ~/.tmda_passwords. If you want to store them in a
# different location you can modify $key_file and $password_file
# below. Just make sure you don't store them inside your web root!
#
# Copyright 2023 Jonathan Kamens <jik@kamens.us>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# See <https://www.gnu.org/licenses/> for  a copy of the GNU General
# Public License.

use CGI qw(:standard :html3 cookie escape autoEscape -nosticky *small);
use CGI::Carp 'fatalsToBrowser';
use Crypt::CBC;
use Errno;
use File::Basename;
use File::HomeDir;
use File::Slurp;
use HTML::Entities;
use MIME::Base64;
use Term::ReadPassword;

my $whoami = basename $0;
my $usage = "Usage: $whoami init | add-password
        If neither is specified, then runs as CGI script.\n";
my $list_chunk_size = 5;
my $cookie_name = "tmda_cookie";
my $key_file = File::HomeDir->my_home . "/.tmda_key";
my $password_file = File::HomeDir->my_home . "/.tmda_passwords";

binmode(STDOUT, ":utf8");

if ($ARGV[0] eq 'init') {
    &create_cbc($key_file);
    exit;
}
elsif ($ARGV[0] eq 'add-password') {
    my %passwords = &read_passwords($password_file);
    &add_password(\%passwords);
    &write_passwords($password_file, \%passwords);
    exit;
}
elsif (@ARGV) {
    die "$whoami: Unrecognized arguments: @ARGV\n$usage";
}
        
my %passwords = &read_passwords($password_file, 1);
my $op = param('op');
my $logged_in = ((-t STDIN) or &check_logged_in);
my $start = (param("s") or 1);
my $list_size = 0;
my $debug = param('debug');

print header(-charset => "utf-8",
             -cookie => &login_cookie);
print start_html("TMDA");

if (! $logged_in) {
    &do_login_form;
}
elsif (!$op or $op eq "list") {
    &do_list;
}
elsif ($op eq "delete") {
    &do_delete;
}
elsif ($op eq "whitelist") {
    &do_whitelist;
}
elsif ($op eq "blacklist") {
    &do_blacklist;
}

if ($logged_in) {
    my $spacer = "&nbsp;";
    print("<p>\n");
    if ($start > 1) {
        print(l("$spacer&lt;&lt;$spacer", "list", s => 1));
        print(l("$spacer&lt;$spacer", "list", s => $start - $list_chunk_size));
    }
    else {
        print("$spacer&lt;&lt;$spacer\n");
        print("$spacer&lt;$spacer\n");
    }
    print(l("Refresh", "list", s => $start));
    my $end_of_list = $start + $list_chunk_size > $list_size;
    if ($end_of_list) {
        print("$spacer&gt;$spacer");
        print("$spacer&gt;&gt;$spacer");
    }
    else {
        my $last_start = int(($list_size - $list_chunk_size + 1) /
                             $list_chunk_size)
            * $list_chunk_size + 1;
        print(l("$spacer&gt;$spacer", "list", s => $start + $list_chunk_size));
        print(l("$spacer&gt;&gt;$spacer", "list", s => $last_start));

    }
    print("</p>\n");
    print("<p>", l("Log out", "logout"));
}

print end_html();

exit;

sub add_password {
    my($passwords) = @_;
    my($username, $password);
    print(STDERR 'Username: ');
    chomp($username = <STDIN>);
    die "No username specified\n" if (! $username);
    die "Username can't contain a colon" if ($username =~ /:/);
    $password = read_password('Password: ');
    die "No password specified\n" if (! $password);
    my $salt = &random_char . &random_char;
    $passwords->{$username} = crypt($password, $salt);
}

sub read_passwords {
    my($password_file, $must_exist) = @_;
    my %passwords;
    if (! open(PASSWORDS, "<", $password_file)) {
        if ($!{ENOENT} and !$must_exist) {
            return;
        }
        die "$password_file: $!\n";
    }
    while (<PASSWORDS>) {
        chomp;
        my($username, $crypt_string) = split(':');
        $passwords{$username} = $crypt_string;
    }
    return %passwords;
}

sub write_passwords {
    my($password_file, $passwords) = @_;
    # To set permissions
    my $new_file = "$password_file.new";
    write_file($new_file, {perms => 0600});
    open(PASSWORDS, ">", $new_file) or die;
    while (my($username, $password) = each %{$passwords}) {
        print(PASSWORDS "$username:$password\n") or die;
    }
    close(PASSWORDS) or die;
    rename($new_file, $password_file) or
        die "rename($new_file, $password_file): $!\n";
    print("Passwords saved in $password_file.\n");
}

sub check_logged_in {
    return undef if (param("op") eq "logout");

    my $username = param("username");
    my $password = param("password");
    if ($username or $password) {
        return(crypt($password, $passwords{$username}) eq
               $passwords{$username} ? $username : undef);
    }

    my $cookie = cookie($cookie_name);
    return undef if (! $cookie);
    $cookie = decode_base64($cookie);
    my $cbc = &get_cbc($key_file);
    my $decrypted = $cbc->decrypt($cookie);
    return $passwords{$decrypted} ? $decrypted : undef;
}

sub do_login_form {
    print("<h1>Login</h1>\n");
    if (param("username") or param("password")) {
        print("<p><strong>Login incorrect.</strong></p>\n");
    }
   
    print("<p><form action='", url(-relative => 1), "' method='post'>\n");
    print("<p><table>\n");
    print("<tr><th>Username:</th><td><input id='username' name='username' ",
          "type='text'/></td></tr>\n");
    print("<tr><th>Password:</th><td><input id='password' name='password' ",
          "type='password'/></td></tr>\n");
    print("</table></p>\n");
    print("<p><input type='submit'/></p>\n");
    print("</form>\n");
}

sub do_list {
    my(%args) = @_;
    my $id, $date, $from, $to, $subject, $index, $count;
    my $pid = open(T, "-|:encoding(utf-8)", "tmda-pending", "--batch",
                   "--summary", "--descending")
        or die;
    while (<T>) {
        if (/^(\d+\.\d+)/) {
            $id = $1;
            next;
        }
        elsif (/^\W+Date:\s+(.*)/) {
            $date = $1;
            next;
        }
        elsif (/^\W+From:\s+(.*)/) {
            $from = $1;
            next;
        }
        elsif (/^\W+To:\s+(.*)/) {
            $to = $1;
            next;
        }
        elsif (/^\W+Subj:\s+(.*)/) {
            $subject = $1;
            next;
        }
        elsif (defined($id) and defined($date) and defined($from) and 
               defined($to) and defined($subject)) {
            # We need this because sometimes immediately after whitelisting an
            # item it shows up in the list output briefly. Ugh.
            next if ($args{-skip} and $args{-skip} eq $id);
            $list_size++;
            if (++$index >= $start) {
                print("<p><table>\n");
                print("<tr><th align='right'>From:</th><td>",
                      e($from), "</td></tr>\n");
                print("<tr><th align='right'>Subject:</th><td>",
                      e($subject), "</td></tr>\n");
                print("<tr><th align='right'>To:</th><td>",
                      e($to), "</td></tr>\n");
                print("<tr><th align='right'>Date:</th><td>",
                      e($date), "</td></tr>\n");
                print("</table>\n");
                print l("Delete", "delete", id => $id, s => $start);
                print l("Whitelist", "whitelist", id => $id, s => $start);
                print l("Blacklist", "blacklist", id => $id, s => $start);
                print("</p>\n");
                last if (++$count == $list_chunk_size);
            }
            $id = $date = $from = $to = $subject = undef;
            next;
        }
    }
    while (<T>) {
        if (/^(\d+\.\d+)/) {
            $list_size++;
        }
    }
    close(T);
}

sub do_queue_operation {
    my($flag, $pattern, $success_str, $failure_str, $skip_list) = @_;

    my $id = param("id");
    my $fh;
    my(@cmd) = ("tmda-pending", "--batch", $flag, $id);
    open($fh, "-|:encoding(utf-8)", @cmd) or die;
    my $output = read_file($fh);
    my $succeeded = (close($fh) and $output =~ /^$pattern /m);
    if ($succeeded) {
        print("<p><strong>$success_str ", encode_entities($id),
              ".</strong></p>\n");
        if ($debug) {
            print("<pre>", encode_entities("@cmd\n$output"), "</pre>\n");
        }
    }
    else {
        print("<p><strong>$failure_str ", encode_entities($id),
              " failed.</strong></p>\n");
        print("<pre>", encode_entities("@cmd\n$output"), "</pre>\n");
    }
    print("<p/>\n");
    &do_list(-skip => $succeeded ? $id : undef) if (! $skip_list);
    return $succeeded;
}

sub do_delete {
    &do_queue_operation("--delete", "delete", "Deleted", "Delete");
}

sub do_whitelist {
    &do_queue_operation("--whitelist", "whitelist", "Whitelisted",
                        "Whitelist");
}

sub do_blacklist {
    &do_queue_operation("--blacklist", "blacklist", "Blacklisted",
                        "Blacklist", 1) and &do_delete;
}

sub e {
    return encode_entities(@_);
}

sub l {
    my($text, $op, %args) = @_;
    $args{"op"} = $op;
    my $t = "<a href=" . url(-relative => 1) . "?";
    my(@args) = map($_ . "=" . escape($args{$_}), keys %args);
    $t .= join("&", @args);
    $t .= ">$text</a>\n";
}

sub create_cbc {
    my($key_file, $silent) = @_;
    my $key = join('', map(&random_char, 0..16));
    my $new_file = "$key_file.new";
    write_file($new_file, {perms => 0600}, $key);
    rename($new_file, $key_file) or
        die "rename($new_file, $key_file): $!\n";
    if (! $silent) {
        print("Cookie encryption key saved in $key_file. Don't forget to\n");
        print("create a username and password with " .
              "\"$whoami add-password\" if necessary.\n");
    }
    return $key;
}

sub get_cbc {
    my($key_file) = @_;
    my $key;
    if ($key = read_file($key_file, {err_mode => "silent"})) {
        chomp $key;
    }
    elsif ($!{ENOENT}) {
        $key = create_cbc($key_file, 1);
    }
    return Crypt::CBC->new(-key => $key, -cipher => "Blowfish");
}

sub login_cookie {
    my $value, $expires;
    my $username = &check_logged_in;
    if (! $username) {
        $value = 0;
        $expires = "-1d";
    }
    else {
        my $cbc = &get_cbc($key_file);
        my $encrypted = $cbc->encrypt($username);
        $value = encode_base64($encrypted, "");
        $expires = "+10y";
    }
    return cookie(-name => $cookie_name,
                  -value => $value,
                  -expires => $expires,
                  -secure => 1);
}

sub random_char {
    ('.', '/', 0..9, 'A'..'Z', 'a'..'z')[rand 64];
}
