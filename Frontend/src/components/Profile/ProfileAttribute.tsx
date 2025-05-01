import { useState } from 'react';
import { Button } from '../Button/Button';
import './ProfileAttribute.css';

interface ProfileAttributeProps {
  label: string;
  value: string | number;
  isEditable?: boolean;
  onUpdate?: (newValue: string) => Promise<void>;
}

export function ProfileAttribute({ 
  label, 
  value, 
  isEditable = false, 
  onUpdate 
}: ProfileAttributeProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState(value.toString());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEdit = () => {
    setInputValue(value.toString());
    setIsEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setInputValue(value.toString());
  };

  const handleSave = async () => {
    if (!onUpdate) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      await onUpdate(inputValue);
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="profile-attribute">
      <div className="attribute-label">{label}</div>
      
      <div className="attribute-content">
        {isEditing ? (
          <div className="attribute-edit">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="attribute-input"
            />
            
            <div className="attribute-actions">
              <Button 
                variant="primary" 
                size="small" 
                onClick={handleSave}
                isLoading={isLoading}
              >
                Save
              </Button>
              <Button 
                variant="ghost" 
                size="small" 
                onClick={handleCancel}
                disabled={isLoading}
              >
                Cancel
              </Button>
            </div>
            
            {error && <div className="attribute-error">{error}</div>}
          </div>
        ) : (
          <div className="attribute-display">
            <div className="attribute-value">{value}</div>
            
            {isEditable && (
              <Button 
                variant="secondary" 
                size="small" 
                onClick={handleEdit}
                className="edit-button"
              >
                Edit
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}