import { writable, derived, type Writable } from 'svelte/store';
import type { 
    Metadata, 
    EntryCreate, 
    Author, 
    AuthorCreate, 
    License, 
    Variable, 
    Keyword,
    DatasourceCreate,
    DetailCreate,
    EntryGroupCreate,
    TemporalScaleBase,
    SpatialScaleBase
} from '../models';

// Main metadata entry store - holds the working copy of the entry being created/edited
export const metadataEntry = writable<EntryCreate>({
    title: '',
    abstract: '',
    external_id: '',
    location: undefined,
    version: 1,
    latest_version_id: undefined,
    is_partial: false,
    comment: '',
    citation: '',
    embargo: false,
    embargo_end: undefined,
    publication: undefined,
    lastUpdate: undefined,
    license: 1, // Default license ID
    variable: 1, // Default variable ID
    author: { first_name: '', last_name: '', is_organisation: false },
    coAuthors: [],
    keywords: [],
    details: [],
    datasource: undefined,
    groups: []
});

// Store for tracking form validation state
export const formValidation = writable<Record<string, boolean>>({
    title: true,
    abstract: true,
    author: true,
    variable: true,
    license: true
});

// Store for tracking which sections are dirty (have unsaved changes)
export const dirtySections = writable<Set<string>>(new Set());

// Store for tracking form submission state
export const submissionState = writable<'idle' | 'submitting' | 'success' | 'error'>('idle');

// Store for submission error messages
export const submissionError = writable<string>('');

// Helper functions for updating the metadata entry
export const metadataActions = {
    // Update basic metadata
    updateBasicInfo: (updates: Partial<Pick<EntryCreate, 'title' | 'abstract' | 'external_id' | 'comment' | 'citation' | 'embargo' | 'is_partial'>>) => {
        metadataEntry.update(entry => ({ ...entry, ...updates }));
        dirtySections.update(sections => {
            sections.add('basic');
            return sections;
        });
    },

    // Update location
    updateLocation: (location: [number, number] | undefined) => {
        const pointLocation = location ? { type: 'Point', coordinates: location } as const : undefined;
        metadataEntry.update(entry => ({ ...entry, location: pointLocation }));
        dirtySections.update(sections => {
            sections.add('location');
            return sections;
        });
    },

    // Update author
    updateAuthor: (author: AuthorCreate | number) => {
        metadataEntry.update(entry => ({ ...entry, author }));
        dirtySections.update(sections => {
            sections.add('author');
            return sections;
        });
    },

    // Add co-author
    addCoAuthor: (coAuthor: AuthorCreate | number) => {
        metadataEntry.update(entry => ({
            ...entry,
            coAuthors: [...(entry.coAuthors || []), coAuthor]
        }));
        dirtySections.update(sections => {
            sections.add('authors');
            return sections;
        });
    },

    // Remove co-author
    removeCoAuthor: (index: number) => {
        metadataEntry.update(entry => ({
            ...entry,
            coAuthors: entry.coAuthors?.filter((_, i) => i !== index) || []
        }));
        dirtySections.update(sections => {
            sections.add('authors');
            return sections;
        });
    },

    // Update co-authors (for reordering)
    updateCoAuthors: (coAuthors: (AuthorCreate | number)[]) => {
        metadataEntry.update(entry => ({
            ...entry,
            coAuthors
        }));
        dirtySections.update(sections => {
            sections.add('authors');
            return sections;
        });
    },

    // Update license
    updateLicense: (license: License | number) => {
        metadataEntry.update(entry => ({ ...entry, license }));
        dirtySections.update(sections => {
            sections.add('license');
            return sections;
        });
    },

    // Update variable
    updateVariable: (variable: number) => {
        metadataEntry.update(entry => ({ ...entry, variable }));
        dirtySections.update(sections => {
            sections.add('variable');
            return sections;
        });
    },

    // Update variable with object (for autocomplete)
    updateVariableObject: (variable: Variable | null) => {
        metadataEntry.update(entry => ({ 
            ...entry, 
            variable: variable?.id || 1 
        }));
        dirtySections.update(sections => {
            sections.add('variable');
            return sections;
        });
    },

    // Add keyword
    addKeyword: (keywordId: number) => {
        metadataEntry.update(entry => ({
            ...entry,
            keywords: [...(entry.keywords || []), keywordId]
        }));
        dirtySections.update(sections => {
            sections.add('keywords');
            return sections;
        });
    },

    // Remove keyword
    removeKeyword: (keywordId: number) => {
        metadataEntry.update(entry => ({
            ...entry,
            keywords: entry.keywords?.filter(id => id !== keywordId) || []
        }));
        dirtySections.update(sections => {
            sections.add('keywords');
            return sections;
        });
    },

    // Add detail
    addDetail: (detail: DetailCreate) => {
        metadataEntry.update(entry => ({
            ...entry,
            details: [...(entry.details || []), detail]
        }));
        dirtySections.update(sections => {
            sections.add('details');
            return sections;
        });
    },

    // Update detail
    updateDetail: (index: number, detail: DetailCreate) => {
        metadataEntry.update(entry => ({
            ...entry,
            details: entry.details?.map((d, i) => i === index ? detail : d) || []
        }));
        dirtySections.update(sections => {
            sections.add('details');
            return sections;
        });
    },

    // Remove detail
    removeDetail: (index: number) => {
        metadataEntry.update(entry => ({
            ...entry,
            details: entry.details?.filter((_, i) => i !== index) || []
        }));
        dirtySections.update(sections => {
            sections.add('details');
            return sections;
        });
    },

    // Update datasource
    updateDatasource: (datasource: DatasourceCreate | undefined) => {
        metadataEntry.update(entry => ({ ...entry, datasource }));
        dirtySections.update(sections => {
            sections.add('datasource');
            return sections;
        });
    },

                    // Create datasource from file upload
                createDatasourceFromUpload: (fileHash: string, filename: string, fileSize: number) => {
                    const datasource: DatasourceCreate = {
                        path: fileHash, // This will be replaced with actual path during metadata creation
                        encoding: 'utf-8',
                        variable_names: [], // Will be populated later
                        args: {},
                        type: 1, // Default type, will be configurable later
                        temporal_scale: undefined,
                        spatial_scale: undefined
                    };
                    
                    metadataEntry.update(entry => ({ ...entry, datasource }));
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

    // Update datasource path (for manual entry)
    updateDatasourcePath: (path: string) => {
        metadataEntry.update(entry => {
            if (entry.datasource) {
                return {
                    ...entry,
                    datasource: { ...entry.datasource, path }
                };
            }
            return entry;
        });
        dirtySections.update(sections => {
            sections.add('datasource');
            return sections;
        });
    },

                    // Clear datasource
                clearDatasource: () => {
                    metadataEntry.update(entry => ({ ...entry, datasource: undefined }));
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

                // Update datasource encoding
                updateDatasourceEncoding: (encoding: string) => {
                    metadataEntry.update(entry => {
                        if (entry.datasource) {
                            return {
                                ...entry,
                                datasource: { ...entry.datasource, encoding }
                            };
                        }
                        return entry;
                    });
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

                // Update datasource variable names
                updateDatasourceVariableNames: (variableNames: string[]) => {
                    metadataEntry.update(entry => {
                        if (entry.datasource) {
                            return {
                                ...entry,
                                datasource: { ...entry.datasource, variable_names: variableNames }
                            };
                        }
                        return entry;
                    });
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

                // Update datasource type
                updateDatasourceType: (type: number | string) => {
                    metadataEntry.update(entry => {
                        if (entry.datasource) {
                            return {
                                ...entry,
                                datasource: { ...entry.datasource, type }
                            };
                        }
                        return entry;
                    });
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

                // Update datasource args
                updateDatasourceArgs: (args: Record<string, any>) => {
                    metadataEntry.update(entry => {
                        if (entry.datasource) {
                            return {
                                ...entry,
                                datasource: { ...entry.datasource, args }
                            };
                        }
                        return entry;
                    });
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

                // Update datasource temporal scale
                updateDatasourceTemporalScale: (temporalScale: TemporalScaleBase | undefined) => {
                    metadataEntry.update(entry => {
                        if (entry.datasource) {
                            return {
                                ...entry,
                                datasource: { ...entry.datasource, temporal_scale: temporalScale }
                            };
                        }
                        return entry;
                    });
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

                // Update datasource spatial scale
                updateDatasourceSpatialScale: (spatialScale: SpatialScaleBase | undefined) => {
                    metadataEntry.update(entry => {
                        if (entry.datasource) {
                            return {
                                ...entry,
                                datasource: { ...entry.datasource, spatial_scale: spatialScale }
                            };
                        }
                        return entry;
                    });
                    dirtySections.update(sections => {
                        sections.add('datasource');
                        return sections;
                    });
                },

    // Add group
    addGroup: (group: number | EntryGroupCreate) => {
        metadataEntry.update(entry => ({
            ...entry,
            groups: [...(entry.groups || []), group]
        }));
        dirtySections.update(sections => {
            sections.add('groups');
            return sections;
        });
    },

    // Remove group
    removeGroup: (index: number) => {
        metadataEntry.update(entry => ({
            ...entry,
            groups: entry.groups?.filter((_, i) => i !== index) || []
        }));
        dirtySections.update(sections => {
            sections.add('groups');
            return sections;
        });
    },

    // Reset the entire form
    reset: () => {
        metadataEntry.set({
            title: '',
            abstract: '',
            external_id: '',
            location: undefined,
            version: 1,
            latest_version_id: undefined,
            is_partial: false,
            comment: '',
            citation: '',
            embargo: false,
            embargo_end: undefined,
            publication: undefined,
            lastUpdate: undefined,
            license: 1,
            variable: 1,
            author: { first_name: '', last_name: '', is_organisation: false },
            coAuthors: [],
            keywords: [],
            details: [],
            datasource: undefined,
            groups: []
        });
        dirtySections.set(new Set());
        submissionState.set('idle');
        submissionError.set('');
    },

    // Load existing metadata for editing
    loadForEdit: (metadata: Metadata) => {
        const entryCreate: EntryCreate = {
            title: metadata.title,
            abstract: metadata.abstract,
            external_id: metadata.external_id,
            location: metadata.location,
            version: metadata.version,
            latest_version_id: metadata.latest_version_id,
            is_partial: metadata.is_partial,
            comment: metadata.comment,
            citation: metadata.citation,
            embargo: metadata.embargo,
            embargo_end: metadata.embargo_end,
            publication: metadata.publication,
            lastUpdate: metadata.lastUpdate,
            license: metadata.license?.id || 1,
            variable: metadata.variable.id,
            author: metadata.author,
            coAuthors: metadata.coAuthors,
            keywords: metadata.keywords.map(k => k.id).filter(id => id !== undefined) as number[],
            details: metadata.details.map(d => ({
                key: d.key,
                stem: d.stem,
                title: d.title,
                raw_value: d.raw_value,
                description: d.description,
                thesaurus: undefined // ThesaurusBase doesn't have id, would need to be handled differently
            })),
            datasource: metadata.datasource ? {
                path: metadata.datasource.path,
                encoding: metadata.datasource.encoding,
                variable_names: metadata.datasource.variable_names,
                args: metadata.datasource.args,
                type: metadata.datasource.type.id || 1,
                temporal_scale: metadata.datasource.temporal_scale,
                spatial_scale: metadata.datasource.spatial_scale
            } : undefined,
            groups: []
        };
        
        metadataEntry.set(entryCreate);
        dirtySections.set(new Set());
        submissionState.set('idle');
        submissionError.set('');
    },

    // Mark section as clean (saved)
    markSectionClean: (section: string) => {
        dirtySections.update(sections => {
            sections.delete(section);
            return sections;
        });
    },

    // Check if form has unsaved changes
    hasUnsavedChanges: derived(dirtySections, ($dirtySections) => $dirtySections.size > 0)
};

// Derived store to check if the form is valid
export const isFormValid = derived(
    [metadataEntry, formValidation],
    ([$metadataEntry, $formValidation]) => {
        return $metadataEntry.title.trim() !== '' &&
               $metadataEntry.abstract.trim() !== '' &&
               ($metadataEntry.author && 
                (typeof $metadataEntry.author === 'object' ? 
                 ($metadataEntry.author.first_name?.trim() !== '' || $metadataEntry.author.last_name?.trim() !== '') :
                 true)) &&
               Object.values($formValidation).every(valid => valid);
    }
);

// Derived store to get the current entry as a clean object (without undefined values)
export const cleanEntry = derived(metadataEntry, ($metadataEntry) => {
    const clean: any = { ...$metadataEntry };
    
    // Remove undefined values
    Object.keys(clean).forEach(key => {
        if (clean[key] === undefined) {
            delete clean[key];
        }
    });
    
    // Clean up arrays
    if (clean.coAuthors && clean.coAuthors.length === 0) {
        delete clean.coAuthors;
    }
    if (clean.keywords && clean.keywords.length === 0) {
        delete clean.keywords;
    }
    if (clean.details && clean.details.length === 0) {
        delete clean.details;
    }
    if (clean.groups && clean.groups.length === 0) {
        delete clean.groups;
    }
    
    return clean;
}); 