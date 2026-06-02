#!/usr/bin/env php
<?php
/**
 * Time & Timezone Helper
 * Cross-platform script for Claude Code skill
 * Works on Windows, Mac, and Linux
 *
 * @version 1.0.0
 * @author SubsHero Team
 */

// Error handling
error_reporting(E_ALL);
ini_set('display_errors', 0);

function showUsage()
{
    echo "Time & Timezone Helper - Cross-Platform Script\n";
    echo "===============================================\n\n";
    echo "USAGE:\n";
    echo "  php time-helper.php <command> [arguments]\n\n";
    echo "COMMANDS:\n";
    echo "  now <timezone>                    Get current time in timezone\n";
    echo "  convert <time> <from_tz> <to_tz>  Convert time between timezones\n";
    echo "  add <offset> [base_time]          Add time offset (5 hours, 30 days, 2 weeks)\n";
    echo "  subtract <offset> [base_time]     Subtract time offset\n";
    echo "  list [filter]                     List available timezones (optional filter)\n";
    echo "  dst <timezone>                    Check if timezone is in DST\n";
    echo "  help                              Show this help message\n\n";
    echo "EXAMPLES:\n";
    echo "  php time-helper.php now \"Asia/Tokyo\"\n";
    echo "  php time-helper.php convert \"15:00\" \"America/New_York\" \"Asia/Tokyo\"\n";
    echo "  php time-helper.php add \"5 hours\"\n";
    echo "  php time-helper.php subtract \"30 days\"\n";
    echo "  php time-helper.php list \"America\"\n";
    echo "  php time-helper.php dst \"America/New_York\"\n\n";
    exit(0);
}

function getCurrentTime($timezone)
{
    try {
        $tz = new DateTimeZone($timezone);
        $dt = new DateTimeImmutable('now', $tz);

        echo "Current time in {$timezone}:\n";
        echo "  " . $dt->format('l, F j, Y - g:i:s A T') . "\n";
        echo "  UTC Offset: " . $dt->format('P') . "\n";
        echo "  Unix Timestamp: " . $dt->getTimestamp() . "\n";
    } catch (Exception $e) {
        echo "Error: Invalid timezone '{$timezone}'\n";
        echo "Use 'list' command to see available timezones\n";
        exit(1);
    }
}

function convertTime($time, $fromTz, $toTz)
{
    try {
        $dt = new DateTimeImmutable($time, new DateTimeZone($fromTz));

        echo "Original Time:\n";
        echo "  " . $dt->format('g:i A T') . "\n";
        echo "  " . $dt->format('l, F j, Y') . "\n";
        echo "  Timezone: {$fromTz}\n\n";

        $dtConverted = $dt->setTimezone(new DateTimeZone($toTz));

        echo "Converted Time:\n";
        echo "  " . $dtConverted->format('g:i A T') . "\n";
        echo "  " . $dtConverted->format('l, F j, Y') . "\n";
        echo "  Timezone: {$toTz}\n\n";

        $offset1 = $dt->format('P');
        $offset2 = $dtConverted->format('P');
        echo "UTC Offsets: {$offset1} -> {$offset2}\n";

        if ($dt->format('Y-m-d') !== $dtConverted->format('Y-m-d')) {
            echo "Note: Date changes during conversion\n";
        }
    } catch (Exception $e) {
        echo "Error: {$e->getMessage()}\n";
        exit(1);
    }
}

function addTime($offset, $baseTime = null)
{
    try {
        $dt = $baseTime ? new DateTimeImmutable($baseTime) : new DateTimeImmutable('now');
        $modified = $dt->modify("+{$offset}");

        if ($modified === false) {
            throw new Exception("Invalid offset format: {$offset}");
        }

        echo "Base Time:\n";
        echo "  " . $dt->format('l, F j, Y - g:i:s A T') . "\n\n";

        echo "Adding: {$offset}\n\n";

        echo "Result:\n";
        echo "  " . $modified->format('l, F j, Y - g:i:s A T') . "\n\n";

        $diff = $dt->diff($modified);
        echo "Time Difference:\n";
        if ($diff->y > 0) echo "  Years: {$diff->y}\n";
        if ($diff->m > 0) echo "  Months: {$diff->m}\n";
        if ($diff->d > 0) echo "  Days: {$diff->d}\n";
        if ($diff->h > 0) echo "  Hours: {$diff->h}\n";
        if ($diff->i > 0) echo "  Minutes: {$diff->i}\n";
        if ($diff->s > 0) echo "  Seconds: {$diff->s}\n";
    } catch (Exception $e) {
        echo "Error: {$e->getMessage()}\n";
        exit(1);
    }
}

function subtractTime($offset, $baseTime = null)
{
    try {
        $dt = $baseTime ? new DateTimeImmutable($baseTime) : new DateTimeImmutable('now');
        $modified = $dt->modify("-{$offset}");

        if ($modified === false) {
            throw new Exception("Invalid offset format: {$offset}");
        }

        echo "Base Time:\n";
        echo "  " . $dt->format('l, F j, Y - g:i:s A T') . "\n\n";

        echo "Subtracting: {$offset}\n\n";

        echo "Result:\n";
        echo "  " . $modified->format('l, F j, Y - g:i:s A T') . "\n\n";

        $diff = $modified->diff($dt);
        echo "Time Difference:\n";
        if ($diff->y > 0) echo "  Years: {$diff->y}\n";
        if ($diff->m > 0) echo "  Months: {$diff->m}\n";
        if ($diff->d > 0) echo "  Days: {$diff->d}\n";
        if ($diff->h > 0) echo "  Hours: {$diff->h}\n";
        if ($diff->i > 0) echo "  Minutes: {$diff->i}\n";
        if ($diff->s > 0) echo "  Seconds: {$diff->s}\n";
    } catch (Exception $e) {
        echo "Error: {$e->getMessage()}\n";
        exit(1);
    }
}

function listTimezones($filter = null)
{
    $timezones = DateTimeZone::listIdentifiers();

    if ($filter) {
        $timezones = array_filter($timezones, function($tz) use ($filter) {
            return stripos($tz, $filter) !== false;
        });
        $timezones = array_values($timezones);
    }

    $title = $filter ? "Available Timezones (filtered by '{$filter}')" : "All Available Timezones";
    echo "{$title}:\n";
    echo str_repeat("=", 50) . "\n";

    if (empty($timezones)) {
        echo "  No timezones found matching '{$filter}'\n";
    } else {
        $grouped = [];
        foreach ($timezones as $tz) {
            $parts = explode('/', $tz);
            $continent = $parts[0];
            if (!isset($grouped[$continent])) {
                $grouped[$continent] = [];
            }
            $grouped[$continent][] = $tz;
        }

        foreach ($grouped as $continent => $tzList) {
            echo "\n";
            echo "  {$continent} (" . count($tzList) . " timezone" . (count($tzList) > 1 ? 's' : '') . "):\n";

            $displayCount = min(20, count($tzList));
            for ($i = 0; $i < $displayCount; $i++) {
                echo "     • {$tzList[$i]}\n";
            }

            if (count($tzList) > 20) {
                $remaining = count($tzList) - 20;
                echo "     ... and {$remaining} more\n";
            }
        }

        echo "\n";
        echo str_repeat("-", 50) . "\n";
        echo "Total: " . count($timezones) . " timezone(s)\n";
    }
}

function checkDST($timezone)
{
    try {
        $tz = new DateTimeZone($timezone);
        $dt = new DateTimeImmutable('now', $tz);
        $transitions = $tz->getTransitions($dt->getTimestamp(), $dt->getTimestamp());

        if (empty($transitions)) {
            echo "DST information not available for {$timezone}\n";
            return;
        }

        $isDST = $transitions[0]['isdst'];

        echo "Timezone: {$timezone}\n";
        echo "  Current time: " . $dt->format('Y-m-d H:i:s T') . "\n";
        echo "  DST Active: " . ($isDST ? "Yes (Daylight Saving Time)" : "No (Standard Time)") . "\n";
        echo "  UTC Offset: " . $dt->format('P') . "\n";
        echo "  Abbreviation: " . $transitions[0]['abbr'] . "\n";

        $futureTransitions = $tz->getTransitions($dt->getTimestamp(), $dt->getTimestamp() + (365 * 24 * 60 * 60));
        if (count($futureTransitions) > 1) {
            $nextTransition = $futureTransitions[1];
            $nextDt = new DateTimeImmutable('@' . $nextTransition['ts'], $tz);
            echo "\n";
            echo "Next DST Change:\n";
            echo "  Date: " . $nextDt->format('F j, Y \a\t g:i A') . "\n";
            echo "  Changing to: " . ($nextTransition['isdst'] ? "Daylight Saving Time" : "Standard Time") . "\n";
        }
    } catch (Exception $e) {
        echo "Error: {$e->getMessage()}\n";
        exit(1);
    }
}

// Main Execution
if ($argc < 2) {
    showUsage();
}

$command = strtolower($argv[1]);

switch ($command) {
    case 'now':
        if ($argc < 3) {
            echo "Error: Missing timezone argument\n";
            exit(1);
        }
        getCurrentTime($argv[2]);
        break;

    case 'convert':
        if ($argc < 5) {
            echo "Error: Missing arguments\n";
            exit(1);
        }
        convertTime($argv[2], $argv[3], $argv[4]);
        break;

    case 'add':
        if ($argc < 3) {
            echo "Error: Missing offset argument\n";
            exit(1);
        }
        addTime($argv[2], $argv[3] ?? null);
        break;

    case 'subtract':
    case 'sub':
        if ($argc < 3) {
            echo "Error: Missing offset argument\n";
            exit(1);
        }
        subtractTime($argv[2], $argv[3] ?? null);
        break;

    case 'list':
    case 'ls':
        listTimezones($argv[2] ?? null);
        break;

    case 'dst':
    case 'daylight':
        if ($argc < 3) {
            echo "Error: Missing timezone argument\n";
            exit(1);
        }
        checkDST($argv[2]);
        break;

    case 'help':
    case '--help':
    case '-h':
        showUsage();
        break;

    default:
        echo "Error: Unknown command '{$command}'\n\n";
        showUsage();
}

exit(0);
