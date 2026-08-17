export const communities = [
  { id: 'itsa', name: 'ITSA', fullName: 'IT Students Association', color: '#00d4ff', description: 'Student-led organization for professional, academic, and personality development.' },
  { id: 'ieee', name: 'IEEE', fullName: 'IEEE Student Branch', color: '#006cb5', description: 'Professional body for advancing technology for humanity.' },
  { id: 'codechef', name: 'CodeChef', fullName: 'CodeChef Chapter', color: '#5b4638', description: 'Competitive programming community and practice platform.' },
  { id: 'gdgc', name: 'GDGC', fullName: 'Google Developer Groups on Campus', color: '#4285f4', description: 'Community for developers interested in Google technologies.' },
  { id: 'mlsc', name: 'MLSC', fullName: 'Microsoft Learn Student Chapter', color: '#00a4ef', description: 'Student chapter for Microsoft technologies and cloud computing.' },
  { id: 'gfg', name: 'GFG', fullName: 'GeeksforGeeks Campus Body', color: '#2f8d46', description: 'Platform for computer science resources and coding practice.' },
  { id: 'nscc', name: 'NSCC', fullName: 'Newton School Coding Club', color: '#ff6b00', description: 'Coding community focused on learning and project building.' },
];

export const domainNodes = [
  { id: 'ai', name: 'AI & ML', color: '#00e5ff', connections: ['data', 'cloud', 'research'] },
  { id: 'web', name: 'Web Dev', color: '#aa00ff', connections: ['app', 'cloud'] },
  { id: 'cyber', name: 'Cybersecurity', color: '#f44336', connections: ['cloud', 'iot'] },
  { id: 'iot', name: 'IoT', color: '#00e676', connections: ['ai', 'data', 'cyber'] },
  { id: 'cloud', name: 'Cloud', color: '#2196f3', connections: ['web', 'ai', 'data'] },
  { id: 'data', name: 'Data Science', color: '#ffd600', connections: ['ai', 'cloud'] },
  { id: 'app', name: 'App Dev', color: '#e040fb', connections: ['web'] },
  { id: 'research', name: 'Research', color: '#7c4dff', connections: ['ai', 'data'] },
];
