# Landing Page for Nginx Proxy

Simple HTML + CSS landing page that provides navigation to all applications in the stevei101 ecosystem.

## Features

- ✅ **Clean Design**: Modern, responsive UI with gradient background
- ✅ **App Cards**: Visual cards for each application (agentnav, prompt-vault, cursor-ide)
- ✅ **Quick Links**: Fast access to API docs, health checks, etc.
- ✅ **Responsive**: Works on mobile and desktop
- ✅ **Lightweight**: Pure HTML + CSS (no JavaScript required)

## Structure

```
landing/
├── index.html    # Main landing page
├── styles.css    # Styling
└── README.md     # This file
```

## Customization

### Adding New Apps

Edit `index.html` and add a new `.app-card`:

```html
<div class="app-card">
    <div class="app-icon">🎯</div>
    <h2>New App</h2>
    <p class="app-description">Description of the app</p>
    <div class="app-links">
        <a href="/new-app/" class="btn btn-primary">Open App</a>
    </div>
    <div class="app-info">
        <span class="badge">Category</span>
    </div>
</div>
```

### Styling

Edit `styles.css` to customize:
- Colors: Update CSS variables in `:root`
- Layout: Modify grid and spacing
- Typography: Change font families and sizes

## Routing

The landing page is served at:
- `/` - Landing page (hub)
- `/app/` - agentnav frontend (proxied)
- `/api/` - Backend API (proxied)
- `/prompt-vault/` - Prompt Vault (proxied, if configured)

## Future Enhancements

Optional TypeScript version could add:
- Dynamic app status checking
- Real-time health monitoring
- App search/filtering
- User preferences

For now, HTML + CSS is sufficient and keeps it simple!

