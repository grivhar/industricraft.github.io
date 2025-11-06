import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from updater import UpdateManager

class IndustriCraftLauncher:
    def __init__(self):
        self.appdata = os.getenv('APPDATA')
        self.base_path = Path(self.appdata) / '.Industricraft'
        self.config_file = self.base_path / 'config.json'
        self.update_url = 'https://raw.githubusercontent.com/grivhar/industricraft.github.io/refs/heads/main/launcher_update'
        
        # Créer le dossier base si nécessaire
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialiser le gestionnaire de mise à jour
        self.updater = UpdateManager(self.base_path, self.update_url)
        
        # Charger ou créer la configuration locale
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration locale ou crée une nouvelle"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Configuration par défaut
            default_config = {
                "versions": {
                    "main": "0.0.0",
                    "theme": "0.0.0",
                    "assets": "0.0.0",
                    "versions": "0.0.0",
                    "minecraft": "0.0.0",
                    "autre": "0.0.0"
                },
                "first_launch": True,
                "username": "",
                "last_played": ""
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Sauvegarde la configuration locale"""
        if config is None:
            config = self.config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def check_and_update(self):
        """Vérifie et applique les mises à jour"""
        print("Vérification des mises à jour...")
        
        # Récupérer les informations de mise à jour
        updates_needed = self.updater.check_updates(self.config['versions'])
        
        if updates_needed:
            print(f"\n{len(updates_needed)} mise(s) à jour disponible(s):")
            for component in updates_needed:
                print(f"  - {component}")
            
            # Télécharger et installer les mises à jour
            if self.updater.install_updates(updates_needed):
                # Mettre à jour la configuration locale
                remote_config = self.updater.get_remote_config()
                for component in updates_needed:
                    if component != 'mods':  # Les mods ne nécessitent pas de redémarrage
                        self.config['versions'][component] = remote_config[component]
                
                self.save_config()
                
                # Vérifier si un redémarrage est nécessaire
                if any(c != 'mods' for c in updates_needed):
                    print("\nRedémarrage du launcher pour appliquer les changements...")
                    self.restart()
                else:
                    print("\nMods mis à jour avec succès!")
            else:
                print("Erreur lors de l'installation des mises à jour.")
                return False
        else:
            print("Le launcher est à jour!")
        
        return True
    
    def first_time_setup(self):
        """Installation initiale de tous les composants"""
        print("=== Premier démarrage détecté ===")
        print("Installation des composants...")
        
        components = ['main', 'theme', 'assets', 'versions', 'minecraft', 'autre', 'mods']
        
        if self.updater.install_updates(components):
            # Télécharger NeoForge
            print("\nTéléchargement de NeoForge...")
            if self.updater.download_neoforge():
                print("NeoForge installé avec succès!")
            
            # Mettre à jour la configuration
            remote_config = self.updater.get_remote_config()
            for component in components:
                if component in remote_config:
                    self.config['versions'][component] = remote_config[component]
            
            self.config['first_launch'] = False
            self.save_config()
            
            print("\nInstallation terminée! Redémarrage...")
            self.restart()
        else:
            print("Erreur lors de l'installation initiale.")
            sys.exit(1)
    
    def launch_game(self, username):
        """Lance le jeu Minecraft avec NeoForge"""
        print(f"\nLancement du jeu pour {username}...")
        
        # Sauvegarder le nom d'utilisateur
        self.config['username'] = username
        self.config['last_played'] = self.get_timestamp()
        self.save_config()
        
        # Chemins importants
        minecraft_dir = self.base_path / 'minecraft'
        versions_dir = self.base_path / 'versions'
        mods_dir = self.base_path / 'mods'
        
        # Vérifier que NeoForge est installé
        neoforge_dir = minecraft_dir / 'neoforge'
        if not neoforge_dir.exists():
            print("Erreur: NeoForge n'est pas installé!")
            return False
        
        # Commande de lancement (à adapter selon votre configuration)
        launch_script = minecraft_dir / 'launch.bat'
        if launch_script.exists():
            try:
                subprocess.Popen([str(launch_script), username], 
                               cwd=str(minecraft_dir),
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                print("Jeu lancé avec succès!")
                return True
            except Exception as e:
                print(f"Erreur lors du lancement: {e}")
                return False
        else:
            print(f"Script de lancement introuvable: {launch_script}")
            return False
    
    def open_gui(self):
        """Ouvre l'interface graphique du launcher"""
        from webview_launcher import LauncherGUI
        gui = LauncherGUI(self)
        gui.start()
    
    def restart(self):
        """Redémarre le launcher"""
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    @staticmethod
    def get_timestamp():
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def run(self):
        """Point d'entrée principal du launcher"""
        print("=" * 50)
        print("    IndustriCraft Launcher")
        print("=" * 50)
        
        # Premier lancement
        if self.config['first_launch']:
            self.first_time_setup()
            return
        
        # Vérifier les mises à jour
        if not self.check_and_update():
            print("Impossible de continuer sans mise à jour.")
            sys.exit(1)
        
        # Lancer l'interface graphique
        self.open_gui()


if __name__ == '__main__':
    try:
        launcher = IndustriCraftLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\nLauncher fermé par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErreur critique: {e}")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)