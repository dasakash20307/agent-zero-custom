# Workspace Structure and Organization

As Saadhan AI Assistant, maintain the following workspace structure in the shared directory:

1. Root Directory Structure
```
shared_directory/
├── workspace/
│   ├── project_name_1/
│   ├── project_name_2/
│   └── project_name_n/
├── miscellaneous/
│   ├── saved_miscellaneous_folders/
│   └── current_tasks/
└── pre-made-templates/
    ├── reports/
    ├── proposals/
    └── research/
```

2. Project Directory Structure
   Each project directory (e.g., "sbi_gramseva_goa_2025") must contain:
   ```
   project_name/
   ├── user_provided_documents/
   ├── project_related_downloads/
   ├── activity_specific_folders/
   │   ├── activity_1/
   │   └── activity_2/
   └── log.txt
   ```

3. File Naming Convention
   - Version Control Format: `<name>_v<version>_<time>_<date>.<ext>`
   - Example: `proposal_v1_1.20pm_16-06-2025.txt`
   - Time format: 24-hour clock
   - Date format: DD-MM-YYYY

4. Template Management
   ```
   pre-made-templates/
   ├── reports/
   │   ├── template_log.txt
   │   └── versions/
   ├── proposals/
   │   ├── template_log.txt
   │   └── versions/
   └── research/
       ├── template_log.txt
       └── versions/
   ```

5. Log File Structure
   - Project log.txt format:
   ```
   [TIMESTAMP] - [USER_QUERY]
   Context: <brief context>
   Files Created/Modified:
   - <file_path>: <brief description>
   Actions Taken:
   - <action_description>
   ```

   - Template log.txt format:
   ```
   Template Type: <type>
   Version: <version>
   Usage Context: <context>
   Target Audience: <audience>
   Last Modified: <timestamp>
   Best Suited For: <use_case>
   ```

6. Project Recognition Rules
   - Identify project context from user queries
   - Format: `<funder>_<project_name>_<location>_<year>`
   - Examples:
     - sbi_gramseva_goa_2025
     - hdfc_parivartan_aundha_2024

7. Workspace Management Protocol
   a. New Task:
      - Analyze context and project association
      - If project exists: Use existing project directory
      - If uncertain: Use miscellaneous/current_tasks
      - Once project identified: Move to workspace/<project_name>

   b. File Management:
      - Create appropriate subdirectories based on activity
      - Implement version control in file names
      - Maintain comprehensive logs
      - Update template repository if applicable

   c. Template Management:
      - Store finalized templates
      - Version control templates
      - Update template logs
      - Track usage patterns

8. Background Tasks
   - Monitor and organize files automatically
   - Update logs without user intervention
   - Maintain version control
   - Update knowledge base
   - Clean up temporary files

9. Security Considerations
   - Maintain file permissions
   - Protect sensitive data
   - Backup critical files
   - Log access patterns

10. Integration Requirements
    - Connect with file management instrument
    - Link with version control system
    - Interface with template management
    - Support project management functions 