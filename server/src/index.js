// server/src/index.js
require('dotenv').config();
const express = require('express');
const app = express();
const repsRoute = require('./routes/representatives');
const healthRoute = require('./routes/health');

// Middleware
app.use(express.json());

// Simple request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
  next();
});

// Routes
app.use('/api/representatives', repsRoute);
app.use('/api/health', healthRoute);

// Root endpoint
app.get('/', (req, res) => {
  res.json({ 
    service: 'Civic Representatives API',
    version: '1.0.0',
    endpoints: [
      'GET /api/representatives?zip=XXXXX',
      'GET /api/representatives?zip=XXXXX&level=federal|state|local',
      'GET /api/health'
    ]
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));
