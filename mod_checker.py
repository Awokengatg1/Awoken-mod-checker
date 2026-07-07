import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class GorillaTagModChecker:
    """
    A comprehensive mod checker for Gorilla Tag that scans, validates,
    and analyzes installed mods.
    """
    
    def __init__(self, game_path):
        """Initialize the mod checker with game path"""
        self.game_path = Path(game_path)
        self.mods = []
        self.mod_extensions = ['.dll', '.gtmod', '.zip', '.rar', '.json', '.xml']
        self.conflicts = []
        self.mod_categories = defaultdict(list)
        self.scan_timestamp = None
        
    def scan_bepinex_plugins(self):
        """Scan BepInEx plugins folder for mod files"""
        plugins_path = self.game_path / "BepInEx" / "plugins"
        
        if not plugins_path.exists():
            print(f"❌ BepInEx plugins folder not found at {plugins_path}")
            return False
        
        print(f"🔍 Scanning BepInEx plugins folder...")
        
        try:
            for file in plugins_path.rglob("*"):
                if file.is_file() and file.suffix in self.mod_extensions:
                    mod_info = self._analyze_mod_file(file)
                    self.mods.append(mod_info)
                    self._categorize_mod(mod_info)
            
            self.scan_timestamp = datetime.now().isoformat()
            return True
        except Exception as e:
            print(f"❌ Error scanning plugins: {e}")
            return False
    
    def scan_game_root(self):
        """Scan root game directory for mod configuration files"""
        print(f"🔍 Scanning game root directory...")
        
        try:
            for file in self.game_path.iterdir():
                if file.is_file() and file.suffix in ['.json', '.xml', '.ini', '.cfg']:
                    if 'mod' in file.name.lower() or 'config' in file.name.lower():
                        mod_info = self._analyze_mod_file(file)
                        self.mods.append(mod_info)
                        self._categorize_mod(mod_info)
        except Exception as e:
            print(f"❌ Error scanning game root: {e}")
    
    def _analyze_mod_file(self, file_path):
        """Analyze individual mod file for metadata"""
        try:
            stat = file_path.stat()
            file_hash = self._calculate_file_hash(file_path)
            
            mod_info = {
                "name": file_path.name,
                "type": file_path.suffix,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "hash": file_hash,
                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "status": "✅ Valid" if stat.st_size > 0 else "❌ Empty",
                "is_compressed": file_path.suffix in ['.zip', '.rar', '.7z'],
                "category": self._detect_mod_category(file_path.name)
            }
            
            return mod_info
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path.name}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of mod file for integrity checking"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return "Unable to calculate"
    
    def _detect_mod_category(self, mod_name):
        """Categorize mod based on name patterns"""
        mod_name_lower = mod_name.lower()
        
        categories = {
            "Cosmetics": ["cosmetic", "rigged", "skin", "avatar", "player", "rig"],
            "Gameplay": ["gun", "sword", "weapon", "gameplay", "mechanic"],
            "Maps": ["map", "level", "scene", "environment"],
            "UI": ["ui", "hud", "interface", "menu"],
            "Audio": ["sound", "audio", "music", "voice"],
            "Visual": ["shader", "visual", "effect", "graphics", "particle"],
            "Weather": ["weather", "climate", "sky", "rain", "snow"],
            "Config": ["config", "settings", ".json", ".xml", ".ini"],
            "Utility": ["tool", "utility", "helper", "loader"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in mod_name_lower for keyword in keywords):
                return category
        
        return "Unknown"
    
    def _categorize_mod(self, mod_info):
        """Add mod to category list"""
        if mod_info:
            category = mod_info.get("category", "Unknown")
            self.mod_categories[category].append(mod_info["name"])
    
    def check_mod_integrity(self):
        """Verify all mods have valid file sizes"""
        print(f"🔎 Checking mod integrity...")
        
        issues = []
        for mod in self.mods:
            if mod["status"] == "❌ Empty":
                issues.append({
                    "mod": mod["name"],
                    "issue": "Empty file detected",
                    "severity": "High"
                })
            
            if mod["size_mb"] > 500:
                issues.append({
                    "mod": mod["name"],
                    "issue": f"Unusually large ({mod['size_mb']} MB)",
                    "severity": "Medium"
                })
        
        return issues
    
    def detect_conflicts(self):
        """Detect potential mod conflicts"""
        print(f"⚠️ Analyzing mod conflicts...")
        
        conflicts = []
        
        # Check for duplicate mod types
        seen_categories = defaultdict(int)
        for mod in self.mods:
            category = mod.get("category", "Unknown")
            seen_categories[category] += 1
        
        for category, count in seen_categories.items():
            if count > 1 and category in ["Cosmetics", "Gameplay", "Maps"]:
                mods_in_category = [m["name"] for m in self.mods if m.get("category") == category]
                conflicts.append({
                    "type": "Duplicate Category",
                    "category": category,
                    "count": count,
                    "mods": mods_in_category,
                    "severity": "Medium",
                    "note": f"Multiple {category} mods may conflict"
                })
        
        # Check for known problematic mod combinations
        problematic_pairs = [
            ("cosmetic", "rigged"),
            ("gameplay", "weapon"),
            ("map", "level")
        ]
        
        mod_names_lower = [m["name"].lower() for m in self.mods]
        
        for mod1, mod2 in problematic_pairs:
            has_mod1 = any(mod1 in name for name in mod_names_lower)
            has_mod2 = any(mod2 in name for name in mod_names_lower)
            
            if has_mod1 and has_mod2:
                conflicts.append({
                    "type": "Potential Conflict",
                    "mods": [m["name"] for m in self.mods if mod1 in m["name"].lower() or mod2 in m["name"].lower()],
                    "severity": "High",
                    "note": f"Mods containing '{mod1}' and '{mod2}' may conflict"
                })
        
        self.conflicts = conflicts
        return conflicts
    
    def get_mod_statistics(self):
        """Generate statistics about installed mods"""
        if not self.mods:
            return None
        
        total_size = sum(m["size_bytes"] for m in self.mods)
        avg_size = total_size / len(self.mods) if self.mods else 0
        
        stats = {
            "total_mods": len(self.mods),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_size_mb": round(avg_size / (1024 * 1024), 2),
            "mods_by_category": dict(self.mod_categories),
            "largest_mod": max(self.mods, key=lambda x: x["size_bytes"])["name"] if self.mods else "N/A",
            "largest_mod_size_mb": max((m["size_mb"] for m in self.mods), default=0),
            "integrity_issues": len(self.check_mod_integrity()),
            "conflicts_detected": len(self.conflicts)
        }
        
        return stats
    
    def generate_full_report(self):
        """Generate comprehensive mod checker report"""
        report = {
            "metadata": {
                "scan_timestamp": self.scan_timestamp,
                "game_path": str(self.game_path),
                "checker_version": "1.0.0"
            },
            "summary": {
                "total_mods": len(self.mods),
                "scan_status": "✅ Completed" if self.mods else "⚠️ No mods found"
            },
            "statistics": self.get_mod_statistics(),
            "mods": self.mods,
            "integrity_issues": self.check_mod_integrity(),
            "conflicts": self.conflicts,
            "categories": dict(self.mod_categories)
        }
        
        return report
    
    def export_json(self, filename="mod_report.json"):
        """Export full report to JSON file"""
        report = self.generate_full_report()
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"✅ Report saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting report: {e}")
            return False
    
    def export_csv(self, filename="mod_report.csv"):
        """Export mod list to CSV file"""
        try:
            import csv
            
            with open(filename, 'w', newline='') as f:
                if self.mods:
                    fieldnames = self.mods[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.mods)
                    print(f"✅ CSV report saved to {filename}")
                    return True
            return False
        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")
            return False
    
    def print_summary(self):
        """Print formatted summary to console"""
        print("\n" + "="*60)
        print("🎮 GORILLA TAG MOD CHECKER REPORT")
        print("="*60)
        
        stats = self.get_mod_statistics()
        
        if not stats:
            print("❌ No mods found")
            print("="*60 + "\n")
            return
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Mods: {stats['total_mods']}")
        print(f"  Total Size: {stats['total_size_mb']} MB")
        print(f"  Average Size: {stats['average_size_mb']} MB")
        print(f"  Largest Mod: {stats['largest_mod']} ({stats['largest_mod_size_mb']} MB)")
        
        print(f"\n📂 MODS BY CATEGORY:")
        for category, mods in stats['mods_by_category'].items():
            print(f"  {category}: {len(mods)} mod(s)")
            for mod in mods[:3]:
                print(f"    • {mod}")
            if len(mods) > 3:
                print(f"    • ... and {len(mods) - 3} more")
        
        print(f"\n✅ MOD LIST:")
        for i, mod in enumerate(self.mods, 1):
            print(f"  {i}. {mod['name']}")
            print(f"     Size: {mod['size_mb']} MB | Type: {mod['type']} | Category: {mod['category']}")
            print(f"     Status: {mod['status']}")
            print(f"     Modified: {mod['modified_date']}")
        
        if self.check_mod_integrity():
            print(f"\n⚠️ INTEGRITY ISSUES:")
            for issue in self.check_mod_integrity():
                print(f"  • {issue['mod']}: {issue['issue']} (Severity: {issue['severity']})")
        
        if self.conflicts:
            print(f"\n🚨 POTENTIAL CONFLICTS:")
            for conflict in self.conflicts:
                print(f"  • {conflict['type']}: {conflict['note']}")
                print(f"    Affected Mods: {', '.join(conflict.get('mods', []))}")
                print(f"    Severity: {conflict['severity']}")
        else:
            print(f"\n✅ No conflicts detected!")
        
        print("\n" + "="*60 + "\n")
    
    def validate_game_path(self):
        """Check if provided path is valid Gorilla Tag installation"""
        required_dirs = ["BepInEx", "Gorilla Tag_Data"]
        
        missing = [d for d in required_dirs if not (self.game_path / d).exists()]
        
        if missing:
            print(f"⚠️ Warning: Expected directories not found: {', '.join(missing)}")
            return False
        
        print(f"✅ Valid Gorilla Tag installation detected")
        return True


def main():
    """Main function to run the mod checker"""
    
    # Configure your Gorilla Tag installation path here
    GORILLA_TAG_PATH = "C:/Program Files (x86)/Steam/steamapps/common/Gorilla Tag"
    
    # Alternative paths to try
    alternative_paths = [
        "C:/Program Files/Steam/steamapps/common/Gorilla Tag",
        "D:/SteamLibrary/steamapps/common/Gorilla Tag",
        "./Gorilla Tag"
    ]
    
    print("🎮 Gorilla Tag Mod Checker v1.0.0")
    print("="*60)
    
    # Try to find Gorilla Tag installation
    game_path = None
    
    if Path(GORILLA_TAG_PATH).exists():
        game_path = GORILLA_TAG_PATH
    else:
        print(f"⚠️ Default path not found. Trying alternatives...\n")
        for alt_path in alternative_paths:
            if Path(alt_path).exists():
                print(f"✅ Found Gorilla Tag at: {alt_path}\n")
                game_path = alt_path
                break
    
    if not game_path:
        print("❌ Could not find Gorilla Tag installation!")
        print(f"   Please edit GORILLA_TAG_PATH in the script or enter path manually:")
        game_path = input("   Enter path: ").strip()
        
        if not Path(game_path).exists():
            print("❌ Invalid path provided!")
            return
    
    # Initialize and run checker
    checker = GorillaTagModChecker(game_path)
    
    # Validate the game path
    if not checker.validate_game_path():
        print("⚠️ Warning: This may not be a valid Gorilla Tag installation")
    
    print()
    
    # Perform scans
    checker.scan_bepinex_plugins()
    checker.scan_game_root()
    
    # Analyze mods
    checker.detect_conflicts()
    
    # Display results
    checker.print_summary()
    
    # Export reports
    checker.export_json("mod_report.json")
    
    try:
        checker.export_csv("mod_report.csv")
    except ImportError:
        print("⚠️ CSV export skipped (csv module not available)")
    
    print("✅ Mod checker completed!")


if __name__ == "__main__":
    main()
