import React from 'react';
import { FileText, AlertTriangle, CheckCircle, Lightbulb, Target } from 'lucide-react';

interface StructuredSummary {
  overview: string;
  key_points: string[];
  obligations: string[];
  risks: string[];
  recommendations: string[];
}

interface EnhancedSummaryProps {
  summary: string;
}

const EnhancedSummary: React.FC<EnhancedSummaryProps> = ({ summary }) => {
  // Try to parse the summary as JSON (new format), fallback to plain text (old format)
  let structuredSummary: StructuredSummary | null = null;
  let isLegacyFormat = false;

  try {
    const parsed = JSON.parse(summary);
    if (parsed && typeof parsed === 'object' && parsed.overview) {
      structuredSummary = parsed;
    } else {
      isLegacyFormat = true;
    }
  } catch {
    isLegacyFormat = true;
  }

  // Legacy format - display as simple text
  if (isLegacyFormat) {
    return (
      <div className="space-y-4">
        <div className="bg-base-200/50 rounded-lg p-4 border border-base-300/50">
          <div className="flex items-start space-x-3">
            <div className="bg-primary/20 p-2 rounded-full">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-200 mb-3 text-lg">Document Overview</h4>
              <p className="text-neutral leading-relaxed text-base">{summary}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // New structured format
  return (
    <div className="space-y-8">
      {/* Overview Section */}
      <div className="bg-base-200/50 rounded-lg p-4 border border-base-300/50">
        <div className="flex items-start space-x-3">
          <div className="bg-primary/20 p-2 rounded-full">
            <Target className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-200 mb-3 text-lg">Document Overview</h4>
            <p className="text-neutral leading-relaxed text-base">{structuredSummary?.overview}</p>
          </div>
        </div>
      </div>

      {/* Key Points Section */}
      {structuredSummary?.key_points && structuredSummary.key_points.length > 0 && (
        <div className="bg-info/5 rounded-lg p-4 border border-info/20">
          <div className="flex items-start space-x-3">
            <div className="bg-info/20 p-2 rounded-full">
              <FileText className="h-5 w-5 text-info" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-200 mb-3 text-lg">Key Points</h4>
              <ul className="space-y-2">
                {structuredSummary.key_points.map((point, index) => (
                  <li key={index} className="text-neutral flex items-start space-x-3">
                    <span className="text-info mt-1 font-bold text-lg">•</span>
                    <span className="leading-relaxed">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Obligations Section */}
      {structuredSummary?.obligations && structuredSummary.obligations.length > 0 && (
        <div className="bg-success/5 rounded-lg p-4 border border-success/20">
          <div className="flex items-start space-x-3">
            <div className="bg-success/20 p-2 rounded-full">
              <CheckCircle className="h-5 w-5 text-success" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-200 mb-3 text-lg">Key Obligations</h4>
              <ul className="space-y-2">
                {structuredSummary.obligations.map((obligation, index) => (
                  <li key={index} className="text-neutral flex items-start space-x-3">
                    <span className="text-success mt-1 font-bold text-lg">•</span>
                    <span className="leading-relaxed">{obligation}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Risks Section */}
      {structuredSummary?.risks && structuredSummary.risks.length > 0 && (
        <div className="bg-warning/5 rounded-lg p-4 border border-warning/20">
          <div className="flex items-start space-x-3">
            <div className="bg-warning/20 p-2 rounded-full">
              <AlertTriangle className="h-5 w-5 text-warning" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-200 mb-3 text-lg">Potential Risks</h4>
              <ul className="space-y-2">
                {structuredSummary.risks.map((risk, index) => (
                  <li key={index} className="text-neutral flex items-start space-x-3">
                    <span className="text-warning mt-1 font-bold text-lg">•</span>
                    <span className="leading-relaxed">{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations Section */}
      {structuredSummary?.recommendations && structuredSummary.recommendations.length > 0 && (
        <div className="bg-accent/5 rounded-lg p-4 border border-accent/20">
          <div className="flex items-start space-x-3">
            <div className="bg-accent/20 p-2 rounded-full">
              <Lightbulb className="h-5 w-5 text-accent" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-200 mb-3 text-lg">Recommendations</h4>
              <ul className="space-y-2">
                {structuredSummary.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-neutral flex items-start space-x-3">
                    <span className="text-accent mt-1 font-bold text-lg">•</span>
                    <span className="leading-relaxed">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedSummary;
