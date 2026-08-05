import React from 'react';

const Placeholder = ({ title }) => (
  <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
    <h2 style={{ marginBottom: '16px', color: 'var(--accent-primary)' }}>{title}</h2>
    <p style={{ color: 'var(--text-secondary)' }}>This module is currently under construction and will be implemented next.</p>
  </div>
);

export const Profile = () => <Placeholder title="User Profile" />;
export const Settings = () => <Placeholder title="Settings" />;
export const About = () => <Placeholder title="About Project" />;
