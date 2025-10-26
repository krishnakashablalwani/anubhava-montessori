#!/usr/bin/env python3
"""
Script to add redirect blocker to all HTML files and disable Google Sites scripts
"""
import os
import re
from pathlib import Path

# The redirect blocker script to add
REDIRECT_BLOCKER = '''    <script>
      // ULTRA AGGRESSIVE REDIRECT BLOCKER - BLOCKS ALL NAVIGATION
      (function() {
        'use strict';
        
        var currentHref = window.location.href;
        var blocked = false;
        
        // Store original functions
        var originalPushState = history.pushState;
        var originalReplaceState = history.replaceState;
        
        // Block history API
        history.pushState = function() { console.log('Blocked pushState'); };
        history.replaceState = function() { console.log('Blocked replaceState'); };
        
        // Completely freeze window.location
        Object.defineProperty(window, 'location', {
          configurable: false,
          get: function() {
            return {
              href: currentHref,
              protocol: 'file:',
              host: '',
              hostname: '',
              port: '',
              pathname: currentHref,
              search: '',
              hash: '',
              origin: 'file://',
              replace: function() { console.log('Blocked location.replace'); },
              assign: function() { console.log('Blocked location.assign'); },
              reload: function() { console.log('Blocked location.reload'); },
              toString: function() { return currentHref; },
              valueOf: function() { return currentHref; }
            };
          },
          set: function(value) {
            console.log('Blocked location set to:', value);
          }
        });
        
        // Block window.open
        window.open = function() {
          console.log('Blocked window.open');
          return null;
        };
        
        // Block beforeunload
        window.addEventListener('beforeunload', function(e) {
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          console.log('Blocked beforeunload');
          return false;
        }, true);
        
        // Block all click events that might navigate
        document.addEventListener('click', function(e) {
          var target = e.target;
          while (target) {
            if (target.tagName === 'A' && target.href && target.href.includes('sites.google.com')) {
              e.preventDefault();
              e.stopPropagation();
              e.stopImmediatePropagation();
              console.log('Blocked click on link to:', target.href);
              return false;
            }
            target = target.parentElement;
          }
        }, true);
        
        // Monitor and block meta refresh tags
        setInterval(function() {
          var metas = document.getElementsByTagName('meta');
          for (var i = 0; i < metas.length; i++) {
            if (metas[i].httpEquiv && metas[i].httpEquiv.toLowerCase() === 'refresh') {
              console.log('Removed meta refresh tag');
              metas[i].remove();
            }
          }
        }, 100);
        
        console.log('REDIRECT BLOCKER ACTIVE - All navigation blocked');
      })();
    </script>
'''

def process_html_file(filepath):
    """Process a single HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already processed
        if 'REDIRECT BLOCKER ACTIVE' in content:
            print(f"  Already processed: {filepath.name}")
            return False
        
        # Find the head tag and insert redirect blocker right after it
        pattern = r'(<head>)'
        replacement = r'\1\n' + REDIRECT_BLOCKER
        
        new_content = re.sub(pattern, replacement, content, count=1)
        
        if new_content == content:
            print(f"  Could not find <head> tag in: {filepath.name}")
            return False
        
        # Now find the last </style> tag in the head section and add comment start after it
        # First, find where head ends
        head_end = new_content.find('</head>')
        if head_end == -1:
            print(f"  Could not find </head> tag in: {filepath.name}")
            return False
        
        head_section = new_content[:head_end]
        
        # Find the last </style> in the head section
        last_style_end = head_section.rfind('</style>')
        
        if last_style_end != -1:
            # Find the next <script after the last </style>
            next_script = head_section.find('<script', last_style_end)
            
            if next_script != -1 and next_script < head_end:
                # Insert comment start before the next script
                new_content = (
                    new_content[:next_script] + 
                    '\n    <!--SCRIPTS DISABLED TO PREVENT REDIRECT-->\n    <!--\n    ' +
                    new_content[next_script:]
                )
                
                # Add comment end before </head>
                new_content = new_content.replace('</head>', '    END DISABLED SCRIPTS-->\n  </head>', 1)
        
        # Write the modified content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ Processed: {filepath.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {filepath.name}: {e}")
        return False

def main():
    # Find the base directory
    base_dir = Path(__file__).parent / 'sites.google.com'
    
    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return
    
    # Find all HTML files
    html_files = list(base_dir.rglob('*.html'))
    
    print(f"Found {len(html_files)} HTML files")
    print("Processing files...\n")
    
    processed = 0
    skipped = 0
    errors = 0
    
    for html_file in html_files:
        result = process_html_file(html_file)
        if result:
            processed += 1
        elif result is False:
            skipped += 1
        else:
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total files: {len(html_files)}")
    print(f"  Processed: {processed}")
    print(f"  Skipped (already processed): {skipped}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
