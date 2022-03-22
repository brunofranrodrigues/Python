#!/usr/bin/perl

use strict;

my $filename = $ARGV[0];
my @file = <>;
my (%obj,%stringex);
my ($list, $listacl, $listname, $i);
for(my $z=0;$z<=$#file;$z++) {
	my $line = &trim($file[$z]);
	if ($line =~ /^ip access-list extended (\w+)/) {
		$listname = $1;
		$i = 0;
	} elsif ($line =~ /^no access-list (\d+)/) { 
		$listname = $1;
		$i = 0; 
	}
	$line =~ s/^access-list \d+ //;
	next if not $line =~ /^(permit|deny) (ip|tcp|udp)/;
	next if $line =~ /fragment/;
	my ($acl) = $line;
	my $linenumber = $z+1;
	$listacl->{$listname}->[$i] = "Line $linenumber : $acl";
	$acl =~ s/host (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/$1 0\.0\.0\.0/g;
	$acl =~ s/eq www/eq 80/;
	$acl =~ s/eq smtp/eq 25/;
	$acl =~ s/eq snmp/eq 161/;
	$acl =~ s/eq netbios-ns/eq 137/;
	$acl =~ s/eq netbios-dgm/eq 138/;
	$acl =~ s/eq ntp/eq 123/;
	$acl =~ s/eq domain/eq 53/;
	$acl =~ s/eq ftp-data/eq 20/;
	$acl =~ s/gt (\d+)/$1:65535/g;
	$acl =~ s/eq (\d+)/$1:$1/g;
	$acl =~ s/lt (\d+)/0:$1/g;
	$acl =~ s/range (\d+) (\d+)/$1:$2/g;
	$acl =~ s/ log//;
	my $flag = "NO";
	if ($acl =~ / established/) {
		$flag = "YES";
		$acl =~ s/ established//;
	}
	$acl =~ s/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/$1\/$2/g; 
	$acl =~ s/any/0\.0\.0\.0\/255\.255\.255\.255/g;
	$acl =~ s/(tcp|udp) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})( established)?$/$1 $2 0:65535 $3 0:65535$4/;
	$acl =~ s/(tcp|udp) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/$1 $2 0:65535 $3/;
	$acl =~ s/(tcp|udp) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d+:\d+) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$/$1 $2 $3 $4 0:65535/;
	my ($action,$proto,$source,$spt,$destination,$dpt,$tuple);
	if ($acl =~ /(permit|deny) ip/) {
		($action, $proto, $source, $destination) = split(/ /,$acl);
		$spt = "0:65535";
		$dpt = "0:65535";
	} else {
		($action, $proto, $source, $spt, $destination, $dpt) = split(/ /,$acl);
	}
	$tuple->{$action}->{$proto}->{$source}->{$spt}->{$destination}->{$dpt}->{$flag} = 1;
	
	$list->{$listname}->[$i] = $tuple;
	$i++;
}

foreach my $key (keys %{$list}) {
	for(my $i=0;$i <= $#{$list->{$key}};$i++) {
		for(my $j=0;$j<$i;$j++) {
			my ($ret) = &checktuple($list->{$key}->[$i],$list->{$key}->[$j]);
			if ($ret) {
				print "-------------------------------\n";
				print "$key ". $listacl->{$key}->[$j] ."\n";
				print "$key ". $listacl->{$key}->[$i] ."\n";
			}
		}
	}
}

sub checktuple() {
	my ($tupnow, $tupbefore) = @_;
	my ($act_n, $proto_n, $source_n, $spt_n, $dest_n, $dpt_n, $flag_n) = &getuple($tupnow);
	my ($act_b, $proto_b, $source_b, $spt_b, $dest_b, $dpt_b, $flag_b) = &getuple($tupbefore);
	return if ($proto_n ne $proto_b && $proto_b ne 'ip'); 
	return if (&checkport($spt_n,$spt_b) ne "TRUE");
	return if (&checkport($dpt_n,$dpt_b) ne "TRUE");
	return if (&checkaddress($source_n,$source_b) ne "TRUE");
	return if (&checkaddress($dest_n,$dest_b) ne "TRUE");
	return if ($proto_b eq 'tcp' && $flag_n ne $flag_b);
	return "$proto_n in $proto_b, $source_n in $source_b, $spt_n in $spt_b, dest_n in $dest_b, $dpt_n in $dpt_b and flags $flag_n in $flag_b";
}

sub checkaddress() {
	my ($ip_n, $ip_b) = @_;
	my ($addr_n,$mask_n) = split(/\//,"$ip_n");
	my ($addr_b,$mask_b) = split(/\//,"$ip_b");
	my @oct_addr_n = split(/\./,$addr_n);
	my @oct_addr_b = split(/\./,$addr_b);
	my @oct_mask_n = split(/\./,$mask_n);
	my @oct_mask_b = split(/\./,$mask_b);
	my $t=0;
	for(my $i=0;$i<=3;$i++) {
		if ($oct_addr_b[$i] <= $oct_addr_n[$i] && ($oct_addr_n[$i]+$oct_mask_n[$i]) <= ($oct_addr_b[$i]+$oct_mask_b[$i])) {
	##DEBUG		print "$oct_addr_b[$i] <= $oct_addr_n[$i] && ($oct_addr_n[$i]+$oct_mask_n[$i]) <= ($oct_addr_b[$i]+$oct_mask_b[$i]))\n";
			$t++;
		}
	}
## DEBUG ##
#	if ($t == 4) {
#		print "$ip_n, $ip_b -- $addr_n,$mask_n $addr_b,$mask_b\n";
#	}
#	print "Need to check $addr_n,$mask_n <> $addr_b,$mask_b\n";
###########
	return "TRUE" if ($t eq 4);
}



sub checkport() {
	my ($portn, $portb) = @_;
	my ($portn1,$portn2) = split(/:/,$portn);
	my ($portb1,$portb2) = split(/:/,$portb);
	if (($portn1 >= $portb1) && ($portn2 <= $portb2)) {
		return "TRUE";
	}
}

sub getuple() {
	my ($t) = @_;
	my ($action,$proto,$source,$destination,$spt,$dpt,$flag) = "";
	($action) = keys %{$t}; 
	($proto) = keys %{$t->{$action}}; 
	($source) = keys %{$t->{$action}->{$proto}}; 
	($spt) = keys %{$t->{$action}->{$proto}->{$source}};
	($destination) = keys %{$t->{$action}->{$proto}->{$source}->{$spt}};
	($dpt) = keys %{$t->{$action}->{$proto}->{$source}->{$spt}->{$destination}};
	($flag) = keys %{$t->{$action}->{$proto}->{$source}->{$spt}->{$destination}->{$dpt}};
	return $action,$proto,$source,$spt,$destination,$dpt,$flag;
}

sub trim($)
{
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	$string =~ s/\t/ /g;
	$string =~ s/\s{2,}/ /g;
	return $string;
}

