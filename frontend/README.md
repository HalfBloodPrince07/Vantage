# LocalLens React Frontend

Modern chat interface with multi-user conversations and document chat functionality.

## Quick Start

### Option 1: Automated Setup (Windows)
```bash
setup.bat
```

### Option 2: Manual Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Features

✅ **Multi-User Chat History**
- Conversations grouped by date
- Pin/delete conversations
- Auto-save messages

✅ **Document-Specific Chat**
- Attach documents to conversations
- Search scoped to attached docs
- Visual indicators

✅ **Real-Time Updates**
- SSE thinking steps streaming
- Live status updates

✅ **Polish Features**
- Dark mode with system detection
- Keyboard shortcuts (Ctrl+K, Ctrl+N, etc.)
- Export conversations (MD/JSON)
- Mobile responsive

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool (super fast)
- **Vanilla CSS** - No dependencies
- **EventSource** - SSE streaming

## Available Scripts

```bash
npm run dev      # Start dev server (http://localhost:3000)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Lint code
```

## Project Structure

```
src/
├── components/
│   ├── ChatInterface.jsx    # Main chat UI
│   ├── ChatSidebar.jsx      # Conversation list
│   └── DocumentSelector.jsx # Document attachment
├── hooks/
│   ├── useDarkMode.js       # Dark mode toggle
│   └── useKeyboardShortcuts.js
├── styles/
│   └── dark-mode.css
├── App.jsx
└── main.jsx
```

## Configuration

**Backend URL:** `http://localhost:8000` (via Vite proxy)

To change, edit `vite.config.js`:
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url',
      changeOrigin: true
    }
  }
}
```

## Requirements

- Node.js 16+
- npm or yarn
- Backend running on port 8000

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+K` | Focus search |
| `Ctrl+N` | New chat |
| `Ctrl+Enter` | Submit |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+E` | Export |

## Documentation

See [frontend_setup.md](../frontend_setup.md) for detailed setup and usage guide.

## Troubleshooting

**CORS errors?**
- Backend has CORS enabled by default
- Check backend is running on port 8000

**Port in use?**
- Change port in `vite.config.js`

**Components not loading?**
- Run `npm install` again
- Clear npm cache: `npm cache clean --force`

## License

MIT
