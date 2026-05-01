#!/usr/bin/env python3
"""
Database initialization script for KIT application.
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
        # Create all tables
        db.create_all()
        
        # Check if database is already seeded
        if Skill.query.first() is not None:
            print("Database already initialized. Skipping seed data.")
            return
        
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
            skill = Skill(**skill_data)
            db.session.add(skill)
        
        print("Creating admin user...")
        # Create admin user if doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@kit.local',
                password_hash=generate_password_hash('admin123'),  # Change in production!
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            db.session.add(admin)
            db.session.flush()  # Get admin ID
            
            # Assign all skills to admin
            all_skills = Skill.query.all()
            admin.skills.extend(all_skills)
        
        # Create sample regular user
        sample_user = User.query.filter_by(username='technolog').first()
        if not sample_user:
            technologist = User(
                username='technolog',
                email='technolog@kit.local',
                password_hash=generate_password_hash('technolog123'),
                first_name='Jan',
                last_name='Kowalski',
                role='user'
            )
            db.session.add(technologist)
            db.session.flush()
            
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
                    last_name='Kowalski',
                    role='user'
                )
                db.session.add(technologist)
                db.session.flush()
                
                # Assign relevant skills
                tech_skills = Skill.query.filter(Skill.name.in_([
                    'Modelowanie 3D', 'Wdrożeniowiec', 'Przygotowanie wyceny',
                    'Analiza BOM', 'SharePoint', 'Dokumentacja techniczna'
                ])).all()
                technologist.skills.extend(tech_skills)
            
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

        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database()