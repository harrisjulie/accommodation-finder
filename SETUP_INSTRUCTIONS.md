# GitHub Setup Instructions for harrisjulie/accommodation_finder

## Step 1: Upload the Data Files

1. Go to: https://github.com/harrisjulie/accommodation_finder
2. Click "Add file" → "Upload files"
3. Create a folder structure by:
   - First creating a `data` folder
   - Upload these JSON files into the `data` folder:
     - accommodations.json (160 items)
     - disabilities.json (106 items)
     - limitations.json (99 items)
     - barriers.json (92 items)
     - functions.json (110 items)
     - relationships.json (currently empty, will be built)

All these files are in your `/github_data/` folder ready to upload.

## Step 2: Upload the Main Tool

1. Upload `index.html` to the root of your repository
2. This file is configured to fetch from your GitHub username

## Step 3: Enable GitHub Pages

1. Go to Settings → Pages (left sidebar)
2. Under "Source" select "Deploy from a branch"
3. Select "main" branch and "/ (root)" folder
4. Click Save
5. Wait ~5 minutes for deployment

Your tool will be live at:
**https://harrisjulie.github.io/accommodation_finder/**

## Step 4: Test Your Live Tool

Once deployed, test that:
- [ ] The database loads (you'll see green stats box with counts)
- [ ] All 4 search modes work
- [ ] The full lists show in each category

## File Structure Should Look Like:

```
harrisjulie/accommodation_finder/
├── index.html
├── data/
│   ├── accommodations.json
│   ├── disabilities.json
│   ├── limitations.json
│   ├── barriers.json
│   ├── functions.json
│   └── relationships.json
└── README.md (optional)
```

## How to Update Data

### Using GitHub Web Interface:
1. Click on any JSON file in the `data` folder
2. Click the pencil icon (Edit)
3. Make changes
4. Click "Commit changes"
5. Site updates automatically in ~1 minute

### To Add New Accommodations:
1. Open `data/accommodations.json`
2. Add new entry following this format:
```json
{
  "id": "A161",
  "name": "New accommodation name",
  "category": "Category",
  "description": "Full description"
}
```

## Building Relationships (Critical Next Step)

The `relationships.json` file needs to be populated. Use Claude to help:

### Example Prompts for Claude:

1. **For Each Disability:**
```
"For ADHD (D001), review this list of 160 accommodations and identify which ones would help. Return as a JSON array of accommodation IDs."
```

2. **For Each Accommodation:**
```
"For 'Flexible work schedule' (A001), which of these disabilities would benefit: [list]. Return as JSON."
```

3. **Systematic Approach:**
```
"Create relationships between these 10 disabilities [D001-D010] and these 20 accommodations [A001-A020]. Output as:
{
  "disability_accommodations": {
    "D001": ["A001", "A004", ...],
    "D002": ["A002", "A005", ...]
  }
}"
```

## Troubleshooting

### If data doesn't load:
1. Check browser console (F12) for errors
2. Verify JSON files are valid (no trailing commas)
3. Ensure files are in `/data/` folder
4. Check GitHub Pages is enabled

### If search returns no results:
1. The relationships.json file needs to be populated
2. This connects disabilities → accommodations, etc.

## Quick Test Links

Once deployed, test these direct links:
- Main tool: https://harrisjulie.github.io/accommodation_finder/
- Accommodations data: https://raw.githubusercontent.com/harrisjulie/accommodation_finder/main/data/accommodations.json
- Check all data files load with the raw.githubusercontent.com links

## Next Priority: Build Relationships

The tool is ready but needs relationships to connect:
- Disabilities → Accommodations (most important)
- Limitations → Accommodations  
- Barriers → Accommodations
- Functions → Accommodations

Use the relationship builder helper to systematically create these connections.
