#!/usr/bin/env python3
"""
Database initialization script for KIT - zen.
Creates tables, seeds initial data, and creates admin user.
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app, db
from app.models.user import User
from app.models.skill import Skill
from app.models.project import Project
from app.models.step import Step
from app.models.step_template import StepTemplate
from app.models.project_template import ProjectTemplate

def init_database():
    """Initialize database with seed data"""
    app = create_app()
    
    with app.app_context():
        # Create all tables from models
        db.create_all()
        
        # Create default roles
        from app.models.role import Role
        roles_data = [
            {'name': 'admin', 'display_name': 'Administrator', 'description': 'Administrator systemu'},
            {'name': 'technolog', 'display_name': 'Technolog', 'description': 'Technolog projektant'},
            {'name': 'konstruktor', 'display_name': 'Konstruktor', 'description': 'Konstruktor'},
            {'name': 'wdrożeniowiec', 'display_name': 'Wdrożeniowiec', 'description': 'Wdrożeniowiec zestawów maszyn'},
            {'name': 'qc', 'display_name': 'Kontrola Jakości', 'description': 'Kontroler jakości'},
            {'name': 'zespół', 'display_name': 'Zespół', 'description': 'Członek zespołu'},
        ]
        for role_data in roles_data:
            if not Role.query.filter_by(name=role_data['name']).first():
                role = Role(**role_data)
                db.session.add(role)
        db.session.commit()
        print("Default roles created.")
        
        print("Creating initial skills...")
        skills_data = [
            # Technical skills
            {'name': 'Modelowanie 3D', 'description': 'Umiejętność modelowania 3D w CAD', 'category': 'technical'},
            {'name': 'Inżynieria CAD', 'description': 'Znajomość oprogramowania CAD', 'category': 'technical'},
            {'name': 'Wdrożeniowiec', 'description': 'Wdrożeniowiec zestawów maszyn', 'category': 'technical'},
            {'name': 'Przygotowanie wyceny', 'description': 'Przygotowanie ofert i wycen', 'category': 'technical'},
            {'name': 'Analiza BOM', 'description': 'Analiza list materiałowych', 'category': 'technical'},
            
            # Documentation skills
            {'name': 'SharePoint', 'description': 'Praca z Microsoft SharePoint', 'category': 'documentation'},
            {'name': 'Dokumentacja techniczna', 'description': 'Tworzenie dokumentacji technicznej', 'category': 'documentation'},
            
            # Design skills
            {'name': 'Ilustracje techniczne', 'description': 'Tworzenie ilustracji technicznych', 'category': 'design'},
            {'name': 'Ilustracje konstrukcyjne', 'description': 'Tworzenie rysunków konstrukcyjnych', 'category': 'design'},
            {'name': 'Projektowanie', 'description': 'Projektowanie produktów', 'category': 'design'},
            
            # Management
            {'name': 'Zarządzanie projektem', 'description': 'Kierowanie projektami', 'category': 'management'},
            {'name': 'Kontrola jakości', 'description': 'Kontrola jakości produkcji', 'category': 'management'},
        ]
        
        for skill_data in skills_data:
            if not Skill.query.filter_by(name=skill_data['name']).first():
                skill = Skill(**skill_data)
                db.session.add(skill)
        
        print("Creating admin user...")
        # Import Role model
        from app.models.role import Role
        
        # Get roles
        admin_role = Role.query.filter_by(name='admin').first()
        team_role = Role.query.filter_by(name='zespół').first()
        technolog_role = Role.query.filter_by(name='technolog').first()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@kit.local',
                password_hash=generate_password_hash('admin123'),  # Change in production!
                first_name='System',
                last_name='Administrator'
            )
            db.session.add(admin)
            db.session.flush()  # Get admin ID
            
            # Assign roles to admin
            if admin_role:
                admin.roles.append(admin_role)
            if team_role:
                admin.roles.append(team_role)
            
            # Assign all skills to admin
            all_skills = Skill.query.all()
            admin.skills.extend(all_skills)
        
        # Create sample regular user (technologist)
        sample_user = User.query.filter_by(username='technolog').first()
        if not sample_user:
            technologist = User(
                username='technolog',
                email='technolog@kit.local',
                password_hash=generate_password_hash('technolog123'),
                first_name='Jan',
                last_name='Kowalski'
            )
            db.session.add(technologist)
            db.session.flush()
            
            # Assign roles: team member + technologist
            if team_role:
                technologist.roles.append(team_role)
            if technolog_role:
                technologist.roles.append(technolog_role)
            
            # Assign relevant skills
            tech_skills = Skill.query.filter(Skill.name.in_([
                'Modelowanie 3D', 'Wdrożeniowiec', 'Przygotowanie wyceny',
                'Analiza BOM', 'SharePoint', 'Dokumentacja techniczna'
            ])).all()
            technologist.skills.extend(tech_skills)
        
        # Create sample project
        sample_project = Project.query.filter_by(name='Projekt XYZ').first()
        if not sample_project:
            project = Project(
                name='Projekt XYZ',
                description='Przykładowy projekt demonstracyjny',
                priority=2,
                status='active',
                created_by=admin.id
            )
            db.session.add(project)
            db.session.flush()
            
            # Ensure technologist user exists
            technologist = User.query.filter_by(username='technolog').first()
            if not technologist:
                technologist = User(
                    username='technolog',
                    email='technolog@kit.local',
                    password_hash=generate_password_hash('technolog123'),
                    first_name='Jan',
                    last_name='Kowalski'
                )
                db.session.add(technologist)
                db.session.flush()
                
                # Assign roles: team member + technologist
                if team_role:
                    technologist.roles.append(team_role)
                if technolog_role:
                    technologist.roles.append(technolog_role)
                
                # Assign relevant skills
                tech_skills = Skill.query.filter(Skill.name.in_([
                    'Modelowanie 3D', 'Wdrożeniowiec', 'Przygotowanie wyceny',
                    'Analiza BOM', 'SharePoint', 'Dokumentacja techniczna'
                ])).all()
                technologist.skills.extend(tech_skills)
            else:
                # Ensure technologist has necessary roles and skills
                if team_role and team_role not in technologist.roles:
                    technologist.roles.append(team_role)
                if technolog_role and technolog_role not in technologist.roles:
                    technologist.roles.append(technolog_role)
            
            # Create sample steps
            steps_data = [
                {
                    'name': 'Wykonanie modelu 3D',
                    'description': 'Stworzenie modelu 3D komponentu',
                    'step_type': 'model_implementation',
                    'priority': 'high',
                    'estimated_time': 120,
                    'assigned_to': technologist.id
                },
                {
                    'name': 'Przygotowanie dokumentacji',
                    'description': 'Przygotowanie dokumentacji technicznej',
                    'step_type': 'sharepoint_confirmation',
                    'priority': 'normal',
                    'estimated_time': 60,
                    'assigned_to': technologist.id
                }
            ]
            
            for step_data in steps_data:
                step = Step(
                    **step_data,
                    created_by=admin.id,
                    project_id=project.id
                )
                db.session.add(step)
        
        # Commit all changes
        db.session.commit()

        # Now create step templates and project templates if they don't exist
        print("\nCreating step templates and project templates...")

        # Step 2.2: Add required skills (if not already present) - but note: we already created skills above, so skip if they exist.
        # We'll create the skills for the templates if they are missing.

        # Define the skills needed for the templates
        template_skills_data = [
            {'name': 'Modelowanie 3D', 'description': 'Tworzenie modeli 3D', 'category': 'technical'},
            {'name': 'Inżynieria CAD', 'description': 'Znajomość oprogramowania CAD', 'category': 'technical'},
            {'name': 'Wdrożeniowiec', 'description': 'Wdrożeniowiec zestawów maszyn', 'category': 'technical'},
            {'name': 'SharePoint', 'description': 'Praca z Microsoft SharePoint', 'category': 'documentation'},
            {'name': 'Dokumentacja techniczna', 'description': 'Tworzenie dokumentacji technicznej', 'category': 'documentation'},
            {'name': 'Ilustracje techniczne', 'description': 'Tworzenie ilustracji technicznych', 'category': 'design'},
            {'name': 'Ilustracje konstrukcyjne', 'description': 'Tworzenie rysunków konstrukcyjnych', 'category': 'design'},
            {'name': 'Przygotowanie wyceny', 'description': 'Przygotowanie ofert i wycen', 'category': 'management'},
            {'name': 'Analiza BOM', 'description': 'Analiza list materiałowych', 'category': 'technical'},
            {'name': 'Projektowanie', 'description': 'Projektowanie produktów', 'category': 'design'},
        ]

        for skill_data in template_skills_data:
            if not Skill.query.filter_by(name=skill_data['name']).first():
                skill = Skill(**skill_data)
                db.session.add(skill)
        db.session.commit()

        # Step 2.3: Add step templates
        step_templates_data = [
            {
                'name': 'Wykonanie rysunku - konstruktor',
                'step_type': 'illustration_designer',
                'priority': 'normal',
                'estimated_time': 120,
                'description': 'Przygotowanie rysunku technicznego',
                'skills': ['Ilustracje konstrukcyjne', 'Projektowanie']
            },
            {
                'name': 'Wykonanie pliku do kroju - konstruktor',
                'step_type': 'illustration_designer',
                'priority': 'normal',
                'estimated_time': 60,
                'description': 'Przygotowanie pliku DXF/DWG',
                'skills': ['Inżynieria CAD']
            },
            {
                'name': 'Wykonanie BOM - technolog',
                'step_type': 'bom_preparation',
                'priority': 'high',
                'estimated_time': 90,
                'description': 'Lista materiałów BOM',
                'skills': ['Przygotowanie wyceny', 'Analiza BOM']
            },
            {
                'name': 'Wykonanie technologii - technolog',
                'step_type': 'sharepoint_confirmation',
                'priority': 'normal',
                'estimated_time': 180,
                'description': 'Opracowanie procesu technologicznego',
                'skills': ['Dokumentacja techniczna', 'SharePoint']
            },
            {
                'name': 'Przygotowanie dokumentacji - technolog',
                'step_type': 'sharepoint_confirmation',
                'priority': 'normal',
                'estimated_time': 120,
                'description': 'Przygotowanie pełnej dokumentacji',
                'skills': ['Dokumentacja techniczna']
            },
            {
                'name': 'Przygotowanie krok po kroku - wdrożeniowiec',
                'step_type': 'model_implementation',
                'priority': 'normal',
                'estimated_time': 150,
                'description': 'Instrukcja wdrożenia krok po kroku',
                'skills': ['Wdrożeniowiec', 'Modelowanie 3D']
            },
            {
                'name': 'Przygotowanie modelu - wdrożeniowiec',
                'step_type': 'model_implementation',
                'priority': 'normal',
                'estimated_time': 200,
                'description': 'Model 3D do wdrożenia',
                'skills': ['Modelowanie 3D', 'Inżynieria CAD']
            }
        ]

        for data in step_templates_data:
            if StepTemplate.query.filter_by(name=data['name']).first():
                continue
            template = StepTemplate(
                name=data['name'],
                step_type=data['step_type'],
                priority=data['priority'],
                estimated_time=data['estimated_time'],
                description=data['description'],
                created_by=admin.id  # admin is the user we created above
            )
            # Add required skills
            for skill_name in data['skills']:
                skill = Skill.query.filter_by(name=skill_name).first()
                if skill:
                    template.required_skills.append(skill)
            db.session.add(template)
        db.session.commit()

        # Step 2.4: Add project template "Projekt podstawowy"
        if not ProjectTemplate.query.filter_by(name='Projekt podstawowy').first():
            # Get the step templates we just created
            steps = StepTemplate.query.filter(
                StepTemplate.name.in_([
                    'Wykonanie rysunku - konstruktor',
                    'Wykonanie pliku do kroju - konstruktor',
                    'Wykonanie BOM - technolog',
                    'Wykonanie technologii - technolog',
                    'Przygotowanie dokumentacji - technolog',
                    'Przygotowanie krok po kroku - wdrożeniowiec',
                    'Przygotowanie modelu - wdrożeniowiec'
                ])
            ).all()

            project_template = ProjectTemplate(
                name='Projekt podstawowy',
                description='Szablon zawiera wszystkie niezbędne kroki dla typowego projektu',
                created_by=admin.id
            )
            project_template.step_templates.extend(steps)
            db.session.add(project_template)
            db.session.commit()
            print("Utworzono szablon projektu 'Projekt podstawowy'")
        else:
            print("Szablon projektu 'Projekt podstawowy' już istnieje.")

        # Step 2.5: Add three new project templates
        print("\nCreating additional project templates...")

        # Helper function to create step templates for project templates
        def create_step_template(name, step_type, priority, estimated_time, description, skill_names, admin_id):
            """Create a step template with associated skills"""
            template = StepTemplate(
                name=name,
                step_type=step_type,
                priority=priority,
                estimated_time=estimated_time,
                description=description,
                created_by=admin_id
            )
            for skill_name in skill_names:
                skill = Skill.query.filter_by(name=skill_name).first()
                if skill:
                    template.required_skills.append(skill)
            return template

        # Template 1: Analiza zapytania klienta
        template1_steps = [
            create_step_template(
                'Analiza zapytania klienta',
                'client_analysis',
                'high',
                60,
                'Analiza potrzeb i wymagań klienta',
                ['Przygotowanie wyceny', 'Analiza BOM'],
                admin.id
            ),
            create_step_template(
                'Przygotowanie "szacowanych" plików do kroju z informacją o długości łączeń',
                'cut_files_preparation',
                'normal',
                90,
                'Przygotowanie plików do kroju z informacją o długości łączeń',
                ['Inżynieria CAD'],
                admin.id
            ),
            create_step_template(
                'Opracowanie wstępnego BOM',
                'bom_preparation',
                'high',
                120,
                'Wstępna lista materiałów',
                ['Analiza BOM', 'Przygotowanie wyceny'],
                admin.id
            ),
            create_step_template(
                'Oszacowanie czasów produktów',
                'time_estimation',
                'normal',
                60,
                'Szacowanie czasów produkcji',
                ['Przygotowanie wyceny'],
                admin.id
            ),
            create_step_template(
                'Przygotowanie wstępnej wyceny',
                'quote_preparation',
                'high',
                90,
                'Wstępna wycena dla klienta',
                ['Przygotowanie wyceny'],
                admin.id
            ),
            create_step_template(
                'Weryfikacja dostępności materiałów i komponentów',
                'material_verification',
                'normal',
                45,
                'Sprawdzenie dostępności materiałów',
                ['Analiza BOM'],
                admin.id
            ),
            create_step_template(
                'Konsultacja z technologiem',
                'technologist_consultation',
                'normal',
                30,
                'Konsultacja z technologiem',
                ['Dokumentacja techniczna'],
                admin.id
            )
        ]

        for step in template1_steps:
            if not StepTemplate.query.filter_by(name=step.name).first():
                db.session.add(step)
        db.session.commit()

        # Create Project Template 1
        if not ProjectTemplate.query.filter_by(name='Szablon 1 - Analiza zapytania').first():
            pt1 = ProjectTemplate(
                name='Szablon 1 - Analiza zapytania',
                description='Szablon dla projektów wymagających analizy zapytania klienta i wstępnego szacowania',
                created_by=admin.id
            )
            pt1.step_templates.extend(template1_steps)
            db.session.add(pt1)
            db.session.commit()
            print("Utworzono szablon projektu 'Szablon 1 - Analiza zapytania'")
        else:
            print("Szablon projektu 'Szablon 1 - Analiza zapytania' już istnieje.")

        # Template 2: Tłumaczenie rysunku
        template2_steps = [
            create_step_template(
                'Tłumaczenie rysunku + weryfikacja, czy są wszystkie istotne informacje',
                'drawing_translation',
                'high',
                120,
                'Tłumaczenie i weryfikacja rysunku technicznego',
                ['Ilustracje konstrukcyjne', 'Inżynieria CAD', 'Projektowanie'],
                admin.id
            ),
            create_step_template(
                'Opracowanie plików do kroju',
                'cut_files_development',
                'normal',
                90,
                'Przygotowanie plików do kroju laserowego/plazmowego',
                ['Inżynieria CAD'],
                admin.id
            ),
            create_step_template(
                'Przygotowanie układu (na 1 szt. i na najbardziej optymalną ilość)',
                'layout_preparation',
                'normal',
                60,
                'Optymalizacja układu na arkuszu',
                ['Inżynieria CAD', 'Projektowanie'],
                admin.id
            ),
            create_step_template(
                'Przygotowanie schematu łączenia',
                'connection_schema',
                'normal',
                90,
                'Schemat połączeń elektrycznych/mechanicznych',
                ['Inżynieria CAD', 'Ilustracje techniczne'],
                admin.id
            ),
            create_step_template(
                'Opracowanie BOM w ERP',
                'bom_erp',
                'high',
                120,
                'Wprowadzenie BOM do systemu ERP',
                ['Analiza BOM', 'SharePoint'],
                admin.id
            ),
            create_step_template(
                'Ustalenie czasów produkcji z odpowiednim podziałem na procesy',
                'production_time',
                'normal',
                90,
                'Szacowanie czasów produkcji z podziałem na etapy',
                ['Przygotowanie wyceny', 'Zarządzanie projektem'],
                admin.id
            ),
            create_step_template(
                'Wgranie dokumentacji do MobiDoc (informacje o etykiecie i pakowaniu)',
                'upload_mobidoc',
                'normal',
                45,
                'Wgrywanie dokumentacji do systemu MobiDoc',
                ['SharePoint', 'Dokumentacja techniczna'],
                admin.id
            )
        ]

        for step in template2_steps:
            if not StepTemplate.query.filter_by(name=step.name).first():
                db.session.add(step)
        db.session.commit()

        # Create Project Template 2
        if not ProjectTemplate.query.filter_by(name='Szablon 2 - Tłumaczenie rysunku').first():
            pt2 = ProjectTemplate(
                name='Szablon 2 - Tłumaczenie rysunku',
                description='Szablon dla projektów wymagających tłumaczenia rysunków i przygotowania do produkcji',
                created_by=admin.id
            )
            pt2.step_templates.extend(template2_steps)
            db.session.add(pt2)
            db.session.commit()
            print("Utworzono szablon projektu 'Szablon 2 - Tłumaczenie rysunku'")
        else:
            print("Szablon projektu 'Szablon 2 - Tłumaczenie rysunku' już istnieje.")

        # Template 3: Wdrożenie
        template3_steps = [
            create_step_template(
                'Omówienie produktu z konstruktorem i technologiem',
                'product_overview',
                'high',
                60,
                'Omówienie produktu z konstruktorem i technologiem',
                ['Zarządzanie projektem', 'Projektowanie', 'Dokumentacja techniczna'],
                admin.id
            ),
            create_step_template(
                'Produkcja pierwszej szywki',
                'first_sample_production',
                'high',
                180,
                'Produkcja pierwszej szywki',
                ['Modelowanie 3D', 'Wdrożeniowiec'],
                admin.id
            ),
            create_step_template(
                'Kontrola wstępna z konstruktorem i technologiem',
                'preliminary_control',
                'normal',
                90,
                'Kontrola wstępna z participation konstruktora i technologa',
                ['Kontrola jakości', 'Projektowanie', 'Dokumentacja techniczna'],
                admin.id
            ),
            create_step_template(
                'Wykonanie zdjęć',
                'photo_session',
                'normal',
                60,
                'Wykonanie zdjęć produktu',
                ['Ilustracje techniczne', 'Dokumentacja techniczna'],
                admin.id
            ),
            create_step_template(
                'Przygotowanie instrukcji krok po kroku',
                'step_by_step_guide',
                'normal',
                120,
                'Instrukcja krok po kroku',
                ['Wdrożeniowiec', 'Modelowanie 3D', 'Dokumentacja techniczna'],
                admin.id
            ),
            create_step_template(
                'Aktualizacja BOM (w porozumieniu z technologiem)',
                'bom_update',
                'normal',
                60,
                'Aktualizacja BOM',
                ['Analiza BOM', 'Przygotowanie wyceny'],
                admin.id
            ),
            create_step_template(
                'Przygotowanie kompletnej dokumentacji (MobiDoc)',
                'mobidoc_preparation',
                'high',
                150,
                'Kompletna dokumentacja w systemie MobiDoc',
                ['SharePoint', 'Dokumentacja techniczna', 'Wdrożeniowiec'],
                admin.id
            ),
            create_step_template(
                'Akceptacja dokumentacji – spotkanie z konstruktorem, technologiem i liderem produkcji',
                'documentation_approval_meeting',
                'high',
                45,
                'Spotkanie akceptacyjne dokumentacji',
                ['Zarządzanie projektem', 'Kontrola jakości'],
                admin.id
            ),
            create_step_template(
                'Kontrola finalna QC',
                'final_qc_control',
                'high',
                90,
                'Kontrola jakościowa finalna',
                ['Kontrola jakości'],
                admin.id
            ),
            create_step_template(
                'Informacja / przekazanie technologii na dział produkcyjny',
                'technology_transfer',
                'high',
                30,
                'Przekazanie technologii do produkcji',
                ['Wdrożeniowiec', 'Dokumentacja techniczna'],
                admin.id
            )
        ]

        for step in template3_steps:
            if not StepTemplate.query.filter_by(name=step.name).first():
                db.session.add(step)
        db.session.commit()

        # Create Project Template 3
        if not ProjectTemplate.query.filter_by(name='Szablon 3 - Wdrożenie').first():
            pt3 = ProjectTemplate(
                name='Szablon 3 - Wdrożenie',
                description='Szablon dla projektów wdrożeniowych z pełną dokumentacją i akceptacją',
                created_by=admin.id
            )
            pt3.step_templates.extend(template3_steps)
            db.session.add(pt3)
            db.session.commit()
            print("Utworzono szablon projektu 'Szablon 3 - Wdrożenie'")
        else:
            print("Szablon projektu 'Szablon 3 - Wdrożenie' już istnieje.")

        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database()