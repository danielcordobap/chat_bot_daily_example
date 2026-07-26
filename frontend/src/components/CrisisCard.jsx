import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';

export default function CrisisCard({ message, resources }) {
  const { t } = useLanguage();

  return (
    <div className="crisis-card">
      <div className="crisis-card-header">
        <span className="crisis-icon">⚠️</span>
        <div className="crisis-header-text">
          <h3>{t('crisis.title')}</h3>
          <span className="crisis-subtext">{t('crisis.subtitle')}</span>
        </div>
      </div>
      
      <div className="crisis-card-body">
        <p className="crisis-message">{message}</p>
        
        {resources && resources.length > 0 ? (
          <div className="crisis-resources-list">
            <h4>{t('crisis.resourcesTitle')}</h4>
            <ul>
              {resources.map((res, index) => (
                <li key={index} className="crisis-resource-item">
                  <span className="resource-name">{res.name}</span>
                  {res.phone && <span className="resource-phone">{t('crisis.contact')} {res.phone}</span>}
                  {res.hours && <span className="resource-hours">{t('crisis.hours')} {res.hours}</span>}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="crisis-unconfigured-note">
            <p>
              <em>{t('crisis.unconfigured')}</em>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
