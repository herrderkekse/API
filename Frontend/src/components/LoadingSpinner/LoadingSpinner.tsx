import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: number;
  color?: string;
}

export const LoadingSpinner = ({ size = 24, color = 'currentColor' }: LoadingSpinnerProps) => {
  return (
    <div 
      className="loading-spinner"
      style={{ 
        width: size, 
        height: size,
        borderColor: color,
        borderRightColor: 'transparent'
      }}
    />
  );
};