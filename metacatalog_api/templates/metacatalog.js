// currently I can't find a better way for this:
function getEl (selector) {
    const el = htmx.find(selector);
    if (!!el) {
        let val = el.value
        if (val == "") {
            return null
        } 
        return val
    } else {
        return null
    }
}

// get the Author stuff
function getAuthor(index) {
    // try to get the id
    const id = getEl(`input[name="authors.${index}.id"]`);
    if (!!id && id !== "-1") {
        return Number(id)
    }

    // try to get the new data
    const org = getEl(`input[name="authors.${index}.is_organisation"]`); 
    if (!!org) {
        return {
            first_name: getEl(`input[name="authors.${index}.first_name"]`),
            last_name: getEl(`input[name="authors.${index}.last_name"]`),
            organisation_name: getEl(`input[name="authors.${index}.organisation_name"]`),
            organisation_abbrev: getEl(`input[name="authors.${index}.organisation_abbrev"]`),
            affiliation: getEl(`input[name="authors.${index}.affiliation"]`),
            is_organisation: Boolean(org),
        }
    }
    return null
}
function getCoAuthors () {
    const authors = [];
    // there can't be more than 30 authors
    for (let i = 2; i < 30; i++) {
        author = getAuthor(i)
        if (!author) {
            break
        } else {
            authors.push(author)
        }
    }
    return [...authors]
}

// get the detail stuff
function getDetail(index) {
    // try to get the key
    const key = getEl(`input[name="details.${index}.key"]`)
    if (!!key && key !== "") {
        const t = getEl(`input[name="details.${index}.type"]`)
        const v = getEl(`input[name="details.${index}.value"]`)
        const stem = getEl(`input[name="details.${index}.stem"]`)
        let val;
        if (t === "bool") {
            val = v == "true"
        } else if (t === "number") {
            val = Number(v)
        } else {
            val = v
        }
        return {
            key: key,
            stem: stem,
            value: val
        }
    } else {
        return null
    }
}
function getDetails() {
    const details = [];
    for (let i = 1; i < 1000; i++) {
        detail = getDetail(i)
        if (detail) {
            details.push({...detail})
        } else {
            break
        }
    }
    return [...details]
}

// location parser
function getLocation() {
    lon = getEl('input[name="location.lon"]')
    lat = getEl('input[name="location.lat"]')
    if (!!lon && !!lat) {
        return `POINT (${lon} ${lat})`
    } else {
        return null
    }
}

// get the datasource

function getTemporalScale() {
    const isActive = document.querySelector('input[name="add_temporal_scale"]').checked
    if (!isActive) {
        return null
    }
    let dims = getEl('input[name="temporal_scale.dimension_names"]')
    if (!dims) {
        dims = ""
    }
    const dimNames = []
    dims.split(',').forEach(el => dimNames.push(el.trim()));
    return {
        resolution: Number(getEl('input[name="temporal_scale.resolution"]')),
        observation_start: getEl('input[name="temporal_scale.start_time"]'),
        observation_end: getEl('input[name="temporal_scale.end_time"]'),
        dimension_names: dimNames,
        support: 1.0
    }
}
function getSpatialScale() {
    const isActive = document.querySelector('input[name="add_spatial_scale"]').checked
    if (!isActive) {
        return null
    }
    // handle dimension names
    const dimNames = []
    let dims = getEl('input[name="spatial_scale.dimension_names"]')
    if (!dims) {
        dims = ""
    }
    dims.split(',').forEach(el => dimNames.push(el.trim()));
    
    return {
        resolution: Number(getEl('input[name="spatial_scale.resolution"]')),
        extent: getEl('input[name="spatial_scale.extent"]'),
        dimension_names: dimNames,
        support: 1.0
    }
}

// we need type, path optional: args, variable_names, scales
function getDatasource() {
    const varNames = [];
    const v = getEl('input[name="datasource.variable_names"]')
    if (!!v) {
        v.split(',').forEach(el => varNames.push(el.trim()));
    }

    var datasource = {
        path: getEl('input[name="datasource.path"]'),
        type: Number(getEl('select[name="datasource.type_id"] option:checked')),
        variable_names: varNames,
        args: {},
        temporal_scale: getTemporalScale(),
        spatial_scale: getSpatialScale()
    }

    return datasource
}

function validateDatasource(datasource) {
    const errors = []
    if (!datasource.path) {
        errors.push("Datasource has no path")
    }
    if (!datasource.type) {
        errors.push("Datasource has no type")
    }
    if (!datasource.variable_names) {
        errors.push("Datasource has no variable names")
    }
    return errors
}
function validateEntry(entry) {
    const errors = []
    if (!entry.title || entry.title == "") {
        errors.push("Metadata Entry has no title")
    }
    if (!entry.abstract || entry.abstract == "") {
        errors.push("Metadata Entry has no abstract")
    }
    if (!entry.variable) {
        errors.push("Metadata Entry has no variable")
    }

    if (!entry.author) {
        errors.push("The Metadata Entry needs at least a first author.")
    } 
    return errors
}
function getValidationErrors(entry) {
    const errors = validateEntry(entry)
    if (entry.datasource) {
        validateDatasource(entry.datasource).forEach(err => errors.push(err))
    }
    return errors
}
function isValidEntry(entry) {
    const errors = getValidationErrors(entry)
    if (errors.length > 0) {
        return false
    } else {
        return true
    }
}

// get an entry
function getEntry() {
    // first get the datasource    
    var entry = {
        title: getEl('input[name="title"]'),
        abstract: getEl('textarea[name="abstract"]'),
        external_id: getEl('input[name="external_id"]'),
        variable: Number(getEl('select[name="variable_id"] option:checked')),
        license: Number(getEl('select[name="license_id"] option:checked')),
        author: getAuthor(1),
        coAuthors: getCoAuthors(),
        location: getLocation(),
        details: getDetails(),
        datasource: getDatasource(),
        keywords: []
    };
    return entry
}

async function sendEntry(entry, opt= {}) {
    const url = opt.url || '/entries'

    // validate the entry remove the datasoruce if necessary
    const entryErrors = validateEntry(entry)
    let datasourceErrors = []
    if (entry.datasource) {
        datasourceErrors= validateDatasource(entry.datasource)
        if (datasourceErrors.length > 0) {
            entry.datasource = null
        }
    } else {
        datasourceErrors = []
    }
    if (entryErrors.length > 0) {
        return {errors: [...entryErrors, ...datasourceErrors]} 
    }

    response = await fetch(
        url,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(entry)
        }
    )
    .then(response => response.json())

    return response
}
