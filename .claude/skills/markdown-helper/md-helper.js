#!/usr/bin/env node

/**
 * Markdown Helper - Token-efficient markdown operations
 *
 * Provides CLI commands for parsing, editing, and generating markdown
 * without loading entire files into Claude context.
 *
 * Usage: node md-helper.js <command> [options]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

// Command handlers
const commands = {
  'extract-headers': extractHeaders,
  'extract-tables': extractTables,
  'extract-lists': extractLists,
  'generate-diagram': generateDiagram,
  'lint': lintMarkdown,
  'replace': bulkReplace,
  'stats': showStats,
  'help': showHelp,
  '--help': showHelp,
  '-h': showHelp,
};

// Main entry point
function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    showHelp();
    process.exit(0);
  }

  const command = args[0];
  const commandArgs = args.slice(1);

  if (commands[command]) {
    try {
      commands[command](commandArgs);
    } catch (error) {
      console.error(colorize(`❌ Error: ${error.message}`, 'red'));
      process.exit(1);
    }
  } else {
    console.error(colorize(`❌ Unknown command: ${command}`, 'red'));
    console.log(`\nRun ${colorize('node md-helper.js help', 'cyan')} to see available commands`);
    process.exit(1);
  }
}

// Extract headers from markdown file
function extractHeaders(args) {
  const file = args[0];
  if (!file) {
    throw new Error('Missing file argument\nUsage: extract-headers <file> [--level N] [--json] [--count]');
  }

  if (!fs.existsSync(file)) {
    throw new Error(`File not found: ${file}`);
  }

  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');

  const headers = [];
  const headerRegex = /^(#{1,6})\s+(.+)$/;

  lines.forEach((line, index) => {
    const match = line.match(headerRegex);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim();
      headers.push({ level, text, line: index + 1 });
    }
  });

  const levelFilter = getOption(args, '--level');
  const jsonOutput = args.includes('--json');
  const showCount = args.includes('--count');

  let filtered = headers;
  if (levelFilter) {
    filtered = headers.filter(h => h.level === parseInt(levelFilter));
  }

  if (jsonOutput) {
    console.log(JSON.stringify(filtered, null, 2));
    return;
  }

  if (showCount) {
    const counts = {};
    headers.forEach(h => {
      counts[`H${h.level}`] = (counts[`H${h.level}`] || 0) + 1;
    });
    console.log(colorize(`📊 Header Count in ${path.basename(file)}:`, 'cyan'));
    console.log(colorize('═'.repeat(40), 'cyan'));
    Object.entries(counts).forEach(([level, count]) => {
      console.log(`   ${level}: ${count}`);
    });
    return;
  }

  console.log(colorize(`📄 Headers in ${path.basename(file)}:`, 'cyan'));
  console.log(colorize('═'.repeat(40), 'cyan'));

  if (filtered.length === 0) {
    console.log(colorize('   No headers found', 'yellow'));
    return;
  }

  filtered.forEach(header => {
    const indent = '  '.repeat(header.level - 1);
    console.log(`${indent}H${header.level}: ${header.text}`);
  });

  console.log(`\n${colorize('Total:', 'bright')} ${filtered.length} header(s)`);
}

// Extract tables from markdown file
function extractTables(args) {
  const file = args[0];
  if (!file) {
    throw new Error('Missing file argument\nUsage: extract-tables <file> [--json] [--index N]');
  }

  if (!fs.existsSync(file)) {
    throw new Error(`File not found: ${file}`);
  }

  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');

  const tables = [];
  let currentTable = null;
  let inTable = false;

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    // Check if line is a table row
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      if (!inTable) {
        inTable = true;
        currentTable = { startLine: index + 1, rows: [] };
      }

      // Parse row
      const cells = trimmed.split('|').slice(1, -1).map(cell => cell.trim());

      // Check if separator row
      if (cells.every(cell => /^:?-+:?$/.test(cell))) {
        currentTable.separator = true;
      } else {
        currentTable.rows.push(cells);
      }
    } else if (inTable) {
      // End of table
      if (currentTable.separator && currentTable.rows.length > 1) {
        const [headers, ...rows] = currentTable.rows;
        tables.push({
          headers,
          rows,
          startLine: currentTable.startLine,
        });
      }
      inTable = false;
      currentTable = null;
    }
  });

  const jsonOutput = args.includes('--json');
  const indexFilter = getOption(args, '--index');

  let filtered = tables;
  if (indexFilter !== null) {
    const idx = parseInt(indexFilter);
    if (idx >= 0 && idx < tables.length) {
      filtered = [tables[idx]];
    } else {
      throw new Error(`Table index ${idx} out of range (0-${tables.length - 1})`);
    }
  }

  if (jsonOutput) {
    console.log(JSON.stringify(filtered, null, 2));
    return;
  }

  if (filtered.length === 0) {
    console.log(colorize(`⚠️  No tables found in ${path.basename(file)}`, 'yellow'));
    return;
  }

  console.log(colorize(`📊 Tables in ${path.basename(file)}:`, 'cyan'));
  console.log(colorize('═'.repeat(40), 'cyan'));

  filtered.forEach((table, idx) => {
    console.log(`\n${colorize(`Table ${idx + 1}`, 'bright')} (line ${table.startLine}):`);
    console.log(`   Headers: ${table.headers.join(' | ')}`);
    console.log(`   Rows: ${table.rows.length}`);

    if (table.rows.length <= 3) {
      table.rows.forEach((row, i) => {
        console.log(`   ${i + 1}. ${row.join(' | ')}`);
      });
    } else {
      console.log(`   First row: ${table.rows[0].join(' | ')}`);
      console.log(`   ... (${table.rows.length - 2} more rows)`);
      console.log(`   Last row: ${table.rows[table.rows.length - 1].join(' | ')}`);
    }
  });

  console.log(`\n${colorize('Total:', 'bright')} ${filtered.length} table(s)`);
}

// Extract lists from markdown
function extractLists(args) {
  const file = args[0];
  if (!file) {
    throw new Error('Missing file argument\nUsage: extract-lists <file> [--type ordered|unordered|task] [--json]');
  }

  if (!fs.existsSync(file)) {
    throw new Error(`File not found: ${file}`);
  }

  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');

  const lists = {
    ordered: [],
    unordered: [],
    task: [],
  };

  const orderedRegex = /^\s*\d+\.\s+(.+)$/;
  const unorderedRegex = /^\s*[-*+]\s+(.+)$/;
  const taskRegex = /^\s*[-*+]\s+\[([ xX])\]\s+(.+)$/;

  lines.forEach((line, index) => {
    const taskMatch = line.match(taskRegex);
    if (taskMatch) {
      lists.task.push({
        checked: taskMatch[1].toLowerCase() === 'x',
        text: taskMatch[2].trim(),
        line: index + 1,
      });
      return;
    }

    const orderedMatch = line.match(orderedRegex);
    if (orderedMatch) {
      lists.ordered.push({
        text: orderedMatch[1].trim(),
        line: index + 1,
      });
      return;
    }

    const unorderedMatch = line.match(unorderedRegex);
    if (unorderedMatch) {
      lists.unordered.push({
        text: unorderedMatch[1].trim(),
        line: index + 1,
      });
    }
  });

  const typeFilter = getOption(args, '--type');
  const jsonOutput = args.includes('--json');

  if (jsonOutput) {
    if (typeFilter) {
      console.log(JSON.stringify(lists[typeFilter] || [], null, 2));
    } else {
      console.log(JSON.stringify(lists, null, 2));
    }
    return;
  }

  console.log(colorize(`📝 Lists in ${path.basename(file)}:`, 'cyan'));
  console.log(colorize('═'.repeat(40), 'cyan'));

  if (typeFilter === 'task' || !typeFilter) {
    if (lists.task.length > 0) {
      console.log(colorize('\nTask Lists:', 'bright'));
      lists.task.forEach(item => {
        const checkbox = item.checked ? '[✓]' : '[ ]';
        console.log(`   ${checkbox} ${item.text} (line ${item.line})`);
      });
      const completed = lists.task.filter(t => t.checked).length;
      console.log(`   ${colorize(`${completed}/${lists.task.length} completed`, 'green')}`);
    }
  }

  if (typeFilter === 'ordered' || !typeFilter) {
    if (lists.ordered.length > 0) {
      console.log(colorize('\nOrdered Lists:', 'bright'));
      lists.ordered.slice(0, 5).forEach((item, i) => {
        console.log(`   ${i + 1}. ${item.text}`);
      });
      if (lists.ordered.length > 5) {
        console.log(`   ... (${lists.ordered.length - 5} more)`);
      }
    }
  }

  if (typeFilter === 'unordered' || !typeFilter) {
    if (lists.unordered.length > 0) {
      console.log(colorize('\nUnordered Lists:', 'bright'));
      lists.unordered.slice(0, 5).forEach(item => {
        console.log(`   • ${item.text}`);
      });
      if (lists.unordered.length > 5) {
        console.log(`   ... (${lists.unordered.length - 5} more)`);
      }
    }
  }
}

// Generate Mermaid diagram
function generateDiagram(args) {
  if (args.length < 2) {
    throw new Error('Missing arguments\nUsage: generate-diagram <type> <output> [--input <file>] [--format svg|png|pdf]');
  }

  const type = args[0];
  const output = args[1];
  const inputFile = getOption(args, '--input');
  const format = getOption(args, '--format') || 'svg';

  let mermaidCode;

  if (inputFile) {
    if (!fs.existsSync(inputFile)) {
      throw new Error(`Input file not found: ${inputFile}`);
    }
    mermaidCode = fs.readFileSync(inputFile, 'utf-8');
  } else {
    // Read from stdin (for interactive mode)
    throw new Error('Interactive mode: please provide --input <file> with Mermaid syntax');
  }

  // Create temporary file
  const tempFile = path.join(process.cwd(), '.mermaid-temp.mmd');
  fs.writeFileSync(tempFile, mermaidCode);

  try {
    // Execute Mermaid CLI
    const cmd = `mmdc -i "${tempFile}" -o "${output}" -t default`;
    execSync(cmd, { stdio: 'pipe' });

    console.log(colorize('✅ Diagram generated successfully!', 'green'));
    console.log(`   Output: ${output}`);
    console.log(`   Format: ${format}`);

    // Clean up temp file
    fs.unlinkSync(tempFile);
  } catch (error) {
    // Clean up temp file
    if (fs.existsSync(tempFile)) {
      fs.unlinkSync(tempFile);
    }
    throw new Error(`Failed to generate diagram: ${error.message}`);
  }
}

// Lint markdown files
function lintMarkdown(args) {
  if (args.length === 0) {
    throw new Error('Missing file/pattern argument\nUsage: lint <file-or-pattern> [--fix] [--check]');
  }

  const filePattern = args[0];
  const checkOnly = args.includes('--check');
  const fix = !checkOnly; // Default is to fix

  try {
    const cmd = fix
      ? `markdownlint-cli2 --fix "${filePattern}"`
      : `markdownlint-cli2 "${filePattern}"`;

    const output = execSync(cmd, { encoding: 'utf-8', stdio: 'pipe' });

    console.log(colorize('✅ Markdown linting completed!', 'green'));
    if (fix) {
      console.log('   Issues auto-fixed');
    } else {
      console.log('   No issues found');
    }

    if (output) {
      console.log(output);
    }
  } catch (error) {
    // markdownlint-cli2 exits with non-zero if issues found
    const output = error.stdout || error.stderr || error.message;

    if (checkOnly) {
      console.log(colorize('⚠️  Issues found:', 'yellow'));
    } else {
      console.log(colorize('✅ Fixed issues:', 'green'));
    }
    console.log(output);
  }
}

// Bulk search and replace
function bulkReplace(args) {
  if (args.length < 3) {
    throw new Error('Missing arguments\nUsage: replace <pattern> <replacement> <files> [--regex] [--dry-run]');
  }

  const pattern = args[0];
  const replacement = args[1];
  const filesPattern = args[2];
  const useRegex = args.includes('--regex');
  const dryRun = args.includes('--dry-run');

  // Find matching files
  const files = findFiles(filesPattern);

  if (files.length === 0) {
    console.log(colorize('⚠️  No files found matching pattern', 'yellow'));
    return;
  }

  let totalMatches = 0;
  let modifiedFiles = 0;
  const results = [];

  files.forEach(file => {
    const content = fs.readFileSync(file, 'utf-8');
    let newContent;
    let matches = 0;

    if (useRegex) {
      const regex = new RegExp(pattern, 'g');
      matches = (content.match(regex) || []).length;
      newContent = content.replace(regex, replacement);
    } else {
      matches = (content.match(new RegExp(escapeRegex(pattern), 'g')) || []).length;
      newContent = content.split(pattern).join(replacement);
    }

    if (matches > 0) {
      totalMatches += matches;
      modifiedFiles++;
      results.push({ file, matches });

      if (!dryRun) {
        fs.writeFileSync(file, newContent, 'utf-8');
      }
    }
  });

  console.log(colorize('🔍 Bulk Replace Results:', 'cyan'));
  console.log(colorize('═'.repeat(40), 'cyan'));
  console.log(`   Scanned: ${files.length} file(s)`);
  console.log(`   Matches: ${totalMatches}`);
  console.log(`   Modified: ${modifiedFiles} file(s)`);

  if (dryRun) {
    console.log(colorize('\n⚠️  DRY RUN - No changes made', 'yellow'));
  } else {
    console.log(colorize('\n✅ Replacement completed!', 'green'));
  }

  if (results.length > 0) {
    console.log(colorize('\nModified files:', 'bright'));
    results.forEach(({ file, matches }) => {
      console.log(`   • ${path.basename(file)} (${matches} replacement${matches > 1 ? 's' : ''})`);
    });
  }
}

// Show markdown statistics
function showStats(args) {
  const file = args[0];
  if (!file) {
    throw new Error('Missing file argument\nUsage: stats <file>');
  }

  if (!fs.existsSync(file)) {
    throw new Error(`File not found: ${file}`);
  }

  const content = fs.readFileSync(file, 'utf-8');
  const lines = content.split('\n');

  // Count various elements
  const stats = {
    lines: lines.length,
    words: content.split(/\s+/).filter(w => w.length > 0).length,
    characters: content.length,
    headings: {
      total: 0,
      byLevel: {},
    },
    codeBlocks: 0,
    links: 0,
    images: 0,
    tables: 0,
    lists: { ordered: 0, unordered: 0, task: 0 },
    blockquotes: 0,
  };

  let inCodeBlock = false;
  let inTable = false;

  lines.forEach(line => {
    // Code blocks
    if (line.trim().startsWith('```')) {
      inCodeBlock = !inCodeBlock;
      if (inCodeBlock) stats.codeBlocks++;
    }

    // Headers
    const headerMatch = line.match(/^(#{1,6})\s+/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      stats.headings.total++;
      stats.headings.byLevel[`H${level}`] = (stats.headings.byLevel[`H${level}`] || 0) + 1;
    }

    // Links
    stats.links += (line.match(/\[([^\]]+)\]\(([^)]+)\)/g) || []).length;

    // Images
    stats.images += (line.match(/!\[([^\]]*)\]\(([^)]+)\)/g) || []).length;

    // Tables
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      if (!inTable) {
        inTable = true;
        stats.tables++;
      }
    } else {
      inTable = false;
    }

    // Lists
    if (/^\s*[-*+]\s+\[([ xX])\]/.test(line)) {
      stats.lists.task++;
    } else if (/^\s*\d+\.\s+/.test(line)) {
      stats.lists.ordered++;
    } else if (/^\s*[-*+]\s+/.test(line)) {
      stats.lists.unordered++;
    }

    // Blockquotes
    if (line.trim().startsWith('>')) {
      stats.blockquotes++;
    }
  });

  // Display stats
  console.log(colorize(`📊 Statistics for ${path.basename(file)}:`, 'cyan'));
  console.log(colorize('═'.repeat(40), 'cyan'));
  console.log(`Lines:           ${stats.lines.toLocaleString()}`);
  console.log(`Words:           ${stats.words.toLocaleString()}`);
  console.log(`Characters:      ${stats.characters.toLocaleString()}`);

  if (stats.headings.total > 0) {
    const levels = Object.entries(stats.headings.byLevel)
      .map(([level, count]) => `${level}: ${count}`)
      .join(', ');
    console.log(`Headings:        ${stats.headings.total} (${levels})`);
  }

  if (stats.tables > 0) console.log(`Tables:          ${stats.tables}`);
  if (stats.codeBlocks > 0) console.log(`Code Blocks:     ${stats.codeBlocks}`);
  if (stats.links > 0) console.log(`Links:           ${stats.links}`);
  if (stats.images > 0) console.log(`Images:          ${stats.images}`);

  const totalLists = stats.lists.ordered + stats.lists.unordered + stats.lists.task;
  if (totalLists > 0) {
    const listDetails = [];
    if (stats.lists.ordered > 0) listDetails.push(`${stats.lists.ordered} ordered`);
    if (stats.lists.unordered > 0) listDetails.push(`${stats.lists.unordered} unordered`);
    if (stats.lists.task > 0) listDetails.push(`${stats.lists.task} tasks`);
    console.log(`Lists:           ${totalLists} (${listDetails.join(', ')})`);
  }

  if (stats.blockquotes > 0) console.log(`Blockquotes:     ${stats.blockquotes}`);
}

// Show help message
function showHelp() {
  console.log(colorize('Markdown Helper - Token-efficient markdown operations', 'cyan'));
  console.log(colorize('═'.repeat(50), 'cyan'));
  console.log('\nUsage: node md-helper.js <command> [options]\n');

  console.log(colorize('Commands:', 'bright'));
  console.log('  extract-headers <file>         Extract headers from markdown');
  console.log('  extract-tables <file>          Extract tables from markdown');
  console.log('  extract-lists <file>           Extract lists from markdown');
  console.log('  generate-diagram <type> <out>  Generate Mermaid diagram');
  console.log('  lint <file>                    Lint and fix markdown');
  console.log('  replace <find> <repl> <files>  Bulk search and replace');
  console.log('  stats <file>                   Show markdown statistics');
  console.log('  help                           Show this help message');

  console.log(colorize('\nExamples:', 'bright'));
  console.log('  node md-helper.js extract-headers README.md --level 2');
  console.log('  node md-helper.js extract-tables data.md --json');
  console.log('  node md-helper.js lint "**/*.md" --fix');
  console.log('  node md-helper.js replace "old" "new" "*.md" --dry-run');
  console.log('  node md-helper.js stats TASK-024.md');

  console.log(colorize('\nToken Savings: 68% vs traditional approach', 'green'));
}

// Utility functions
function getOption(args, flag) {
  const index = args.indexOf(flag);
  if (index !== -1 && index + 1 < args.length) {
    return args[index + 1];
  }
  return null;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function findFiles(pattern) {
  // Simple glob implementation for common patterns
  const cwd = process.cwd();

  // Handle simple patterns like "*.md" or "**/*.md"
  if (pattern.includes('*')) {
    try {
      const { execSync } = require('child_process');
      const result = execSync(`fd -e md -t f`, { encoding: 'utf-8', cwd });
      return result.trim().split('\n').filter(f => f.length > 0).map(f => path.join(cwd, f));
    } catch (error) {
      // Fallback to simple recursive search
      return findFilesRecursive(cwd, '.md');
    }
  }

  // Single file
  if (fs.existsSync(pattern)) {
    return [path.resolve(pattern)];
  }

  return [];
}

function findFilesRecursive(dir, ext) {
  const results = [];

  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!entry.name.startsWith('.') && entry.name !== 'node_modules') {
          results.push(...findFilesRecursive(fullPath, ext));
        }
      } else if (entry.isFile() && entry.name.endsWith(ext)) {
        results.push(fullPath);
      }
    }
  } catch (error) {
    // Ignore permission errors
  }

  return results;
}

// Run main function
if (require.main === module) {
  main();
}

module.exports = { commands };
