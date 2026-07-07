using BepInEx;
using BepInEx.Configuration;
using UnityEngine;
using System.Collections.Generic;
using System.IO;
using System.Linq;

[BepInPlugin("com.awoken.modchecker", "Mod Checker Menu", "1.0.0")]
public class ModCheckerPlugin : BaseUnityPlugin
{
    private bool showMenu = false;
    private Vector2 scrollPosition = Vector2.zero;
    private List<ModInfo> detectedMods = new List<ModInfo>();
    private ConfigEntry<KeyCode> menuToggleKey;
    private bool modsScanned = false;
    
    // Mod info structure
    private class ModInfo
    {
        public string name;
        public string category;
        public string size;
        public string path;
    }
    
    void Awake()
    {
        // Set up keybind to open menu (default: M)
        menuToggleKey = Config.Bind<KeyCode>("General", "MenuToggle", KeyCode.M, "Key to toggle mod menu");
        
        Logger.LogInfo("Mod Checker initialized! Press M to open menu");
    }
    
    void Update()
    {
        // Toggle menu with key press
        if (Input.GetKeyDown(menuToggleKey.Value))
        {
            showMenu = !showMenu;
            
            // Scan mods when menu opens
            if (showMenu && !modsScanned)
            {
                ScanMods();
                modsScanned = true;
            }
        }
    }
    
    void ScanMods()
    {
        detectedMods.Clear();
        
        string pluginsPath = Path.Combine(Paths.BepInExRootPath, "plugins");
        
        if (Directory.Exists(pluginsPath))
        {
            // Scan for DLL files
            var dllFiles = Directory.GetFiles(pluginsPath, "*.dll", SearchOption.AllDirectories);
            
            foreach (var file in dllFiles)
            {
                FileInfo fileInfo = new FileInfo(file);
                ModInfo modInfo = new ModInfo
                {
                    name = Path.GetFileName(file),
                    path = file,
                    size = GetFileSize(fileInfo.Length),
                    category = CategorizeMod(Path.GetFileName(file))
                };
                
                detectedMods.Add(modInfo);
            }
            
            // Scan for .gtmod files
            var gtmodFiles = Directory.GetFiles(pluginsPath, "*.gtmod", SearchOption.AllDirectories);
            
            foreach (var file in gtmodFiles)
            {
                FileInfo fileInfo = new FileInfo(file);
                ModInfo modInfo = new ModInfo
                {
                    name = Path.GetFileName(file),
                    path = file,
                    size = GetFileSize(fileInfo.Length),
                    category = CategorizeMod(Path.GetFileName(file))
                };
                
                detectedMods.Add(modInfo);
            }
            
            Logger.LogInfo($"✅ Found {detectedMods.Count} mods!");
        }
        else
        {
            Logger.LogWarning($"❌ Plugins folder not found at: {pluginsPath}");
        }
    }
    
    string CategorizeMod(string modName)
    {
        string nameLower = modName.ToLower();
        
        if (nameLower.Contains("cosmetic") || nameLower.Contains("rigged") || nameLower.Contains("skin"))
            return "Cosmetics";
        if (nameLower.Contains("gameplay") || nameLower.Contains("gun") || nameLower.Contains("weapon"))
            return "Gameplay";
        if (nameLower.Contains("map") || nameLower.Contains("level"))
            return "Maps";
        if (nameLower.Contains("weather") || nameLower.Contains("sky"))
            return "Weather";
        if (nameLower.Contains("ui") || nameLower.Contains("hud"))
            return "UI";
        if (nameLower.Contains("audio") || nameLower.Contains("sound"))
            return "Audio";
        if (nameLower.Contains("visual") || nameLower.Contains("shader"))
            return "Visual";
        
        return "Other";
    }
    
    string GetFileSize(long bytes)
    {
        if (bytes < 1024)
            return bytes + " B";
        else if (bytes < 1024 * 1024)
            return (bytes / 1024f).ToString("F1") + " KB";
        else
            return (bytes / (1024f * 1024f)).ToString("F1") + " MB";
    }
    
    void OnGUI()
    {
        if (!showMenu) return;
        
        // Main window background
        GUI.skin.box.normal.background = Texture2D.whiteTexture;
        GUI.backgroundColor = new Color(0.15f, 0.15f, 0.25f, 0.95f);
        GUI.Box(new Rect(Screen.width / 2 - 250, 50, 500, 700), "");
        
        // Title
        GUI.color = new Color(1f, 1f, 0.2f, 1f);
        GUI.Label(new Rect(Screen.width / 2 - 240, 65, 480, 40), "<size=28><b>🎮 MOD CHECKER</b></size>");
        
        // Stats
        GUI.color = new Color(0.5f, 1f, 0.5f, 1f);
        GUI.Label(new Rect(Screen.width / 2 - 240, 105, 480, 25), $"<size=16>Total Mods: <color=yellow>{detectedMods.Count}</color></size>");
        
        // Divider line
        GUI.backgroundColor = new Color(0.5f, 0.5f, 0.5f, 1f);
        GUI.Box(new Rect(Screen.width / 2 - 240, 135, 480, 2), "");
        
        // Mod list with scroll
        GUI.backgroundColor = new Color(0.1f, 0.1f, 0.15f, 0.9f);
        scrollPosition = GUI.BeginScrollView(
            new Rect(Screen.width / 2 - 240, 145, 480, 480), 
            scrollPosition, 
            new Rect(0, 0, 450, detectedMods.Count * 50)
        );
        
        GUI.color = Color.white;
        
        for (int i = 0; i < detectedMods.Count; i++)
        {
            ModInfo mod = detectedMods[i];
            float yPos = i * 50;
            
            // Mod entry background
            GUI.backgroundColor = new Color(0.2f, 0.2f, 0.3f, 0.5f);
            GUI.Box(new Rect(5, yPos, 440, 45), "");
            
            // Mod name and category
            GUI.color = GetCategoryColor(mod.category);
            GUI.Label(new Rect(15, yPos + 2, 300, 20), $"<b>✓ {mod.name}</b>");
            
            GUI.color = new Color(0.7f, 0.7f, 0.7f, 1f);
            GUI.Label(new Rect(15, yPos + 22, 200, 18), $"<size=12>{mod.category}</size>");
            
            GUI.color = new Color(0.9f, 0.9f, 0.9f, 1f);
            GUI.Label(new Rect(300, yPos + 22, 140, 18), $"<size=12>{mod.size}</size>");
        }
        
        GUI.EndScrollView();
        
        // Divider
        GUI.backgroundColor = new Color(0.5f, 0.5f, 0.5f, 1f);
        GUI.Box(new Rect(Screen.width / 2 - 240, 635, 480, 2), "");
        
        // Close button
        GUI.backgroundColor = new Color(0.2f, 0.2f, 0.2f, 1f);
        GUI.color = Color.white;
        
        if (GUI.Button(new Rect(Screen.width / 2 - 240, 645, 480, 40), "<size=16><b>CLOSE (Press M)</b></size>"))
        {
            showMenu = false;
        }
        
        // Info text
        GUI.backgroundColor = new Color(0, 0, 0, 0);
        GUI.color = new Color(0.6f, 0.6f, 0.6f, 1f);
        GUI.Label(new Rect(Screen.width / 2 - 240, 690, 480, 20), "<size=12>Press M to toggle menu | All mods detected from BepInEx/plugins</size>");
    }
    
    Color GetCategoryColor(string category)
    {
        switch (category)
        {
            case "Cosmetics":
                return Color.cyan;
            case "Gameplay":
                return Color.yellow;
            case "Maps":
                return Color.green;
            case "Weather":
                return new Color(0.5f, 1f, 0.5f);
            case "UI":
                return Color.magenta;
            case "Audio":
                return new Color(1f, 0.5f, 1f);
            case "Visual":
                return new Color(1f, 0.8f, 0f);
            default:
                return Color.white;
        }
    }
}
