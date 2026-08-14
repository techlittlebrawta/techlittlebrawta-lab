#!/usr/bin/env php
<?php
declare(strict_types=1);

$labFile = $argv[1] ?? '/opt/unetlab/labs/Tech Little Brawta Lab.unl';
$password = getenv('TLB_LAB_PASSWORD');
if ($password === false || $password === '') {
    if (!function_exists('posix_isatty') || !posix_isatty(STDIN)) {
        fwrite(STDERR, "TLB_LAB_PASSWORD is required when stdin is not a terminal\n");
        exit(2);
    }
    fwrite(STDERR, 'Downstream password: ');
    system('stty -echo');
    $password = rtrim((string) fgets(STDIN), "\r\n");
    system('stty echo');
    fwrite(STDERR, "\n");
}
if (strlen($password) < 8) {
    fwrite(STDERR, "Downstream password does not meet the minimum length\n");
    exit(2);
}

function eosConfig(string $name, int $id, string $password): string {
    $hash = crypt($password, '$6$tlbeos' . $id . '$');
    return "hostname {$name}\nservice routing protocols model multi-agent\n"
        . "username admin privilege 15 role network-admin secret sha512 {$hash}\n"
        . "management ssh\n   no shutdown\ninterface Management1\n"
        . " description OOB-MANAGEMENT\n ip address 10.255.255." . (100 + $id)
        . "/24\n no shutdown\nend\n";
}

function iosConfig(string $name, int $id, string $password): string {
    $hash = crypt($password, '$1$tlbios' . $id . '$');
    return "hostname {$name}\nusername admin privilege 15 secret 5 {$hash}\n"
        . "ip domain name lab.example.com\ncrypto key generate rsa modulus 2048\n"
        . "ip ssh version 2\ninterface GigabitEthernet0/0\n"
        . " description OOB-MANAGEMENT\n vrf forwarding Mgmt-vrf\n ip address 10.255.255."
        . (100 + $id) . " 255.255.255.0\n no shutdown\n"
        . "line vty 0 15\n login local\n transport input ssh\nend\n";
}

function junosConfig(string $name, int $id, string $password): string {
    $hash = crypt($password, '$6$tlbjunos' . $id . '$');
    return "set system host-name {$name}\nset system services ssh\n"
        . "set system root-authentication encrypted-password \"{$hash}\"\n"
        . "set interfaces fxp0 unit 0 family inet address 10.255.255."
        . (100 + $id) . "/24\n";
}

function arubaConfig(string $name, int $id, string $password): string {
    return "hostname {$name}\nuser admin group administrators password plaintext {$password}\n"
        . "ssh server vrf mgmt\ninterface mgmt\n no shutdown\n ip static 10.255.255."
        . (100 + $id) . "/24\n";
}

$dom = new DOMDocument('1.0', 'UTF-8');
$dom->preserveWhiteSpace = false;
$dom->formatOutput = true;
if (!$dom->load($labFile)) {
    fwrite(STDERR, "Unable to load {$labFile}\n");
    exit(2);
}
$configured = [];
foreach ($dom->getElementsByTagName('node') as $node) {
    if (!$node instanceof DOMElement) {
        continue;
    }
    $id = (int) $node->getAttribute('id');
    $name = $node->getAttribute('name');
    $template = $node->getAttribute('template');
    $config = null;
    switch ($template) {
        case 'veos':
            $config = eosConfig($name, $id, $password);
            break;
        case 'cat9kv':
            $config = iosConfig($name, $id, $password);
            break;
        case 'vsrxng':
        case 'vjunosswitch':
            $config = junosConfig($name, $id, $password);
            break;
        case 'arubacx':
            $config = arubaConfig($name, $id, $password);
            break;
    }
    if ($config === null) {
        continue;
    }
    $node->setAttribute('config', '1');
    $node->setAttribute('config_data', base64_encode($config));
    $configured[$id] = $name;
}

$backup = $labFile . '.pre-community-startup-' . gmdate('Ymd-His');
if (!copy($labFile, $backup) || $dom->save($labFile) === false) {
    fwrite(STDERR, "Unable to back up or save the live topology\n");
    exit(3);
}

chdir('/opt/unetlab/html');
require_once 'includes/init.php';
$lab = new Lab($labFile, 43, 4);
foreach ($configured as $id => $name) {
    $nodes = $lab->getNodes();
    if (!isset($nodes[$id])) {
        throw new RuntimeException("Node {$id} disappeared while rendering startup configuration");
    }
    $nodes[$id]->updateStartUpConfig();
}
if ($lab->save() !== 0) {
    fwrite(STDERR, "PNETLab rejected the rendered topology\n");
    exit(3);
}
echo 'rendered=' . count($configured) . ' backup=' . $backup . PHP_EOL;
