import React from 'react';

export const PanelHeader = ({ icon, title, accent, actions }) => (
    <div className="panel-header">
        <div className="panel-header-left">
            <div className="panel-header-icon" style={{ '--accent': accent || '#f5a623' }}>{icon}</div>
            <span className="panel-header-title">{title}</span>
        </div>
        <div className="panel-header-actions">{actions}</div>
    </div>
);