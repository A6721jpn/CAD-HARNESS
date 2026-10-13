"""v3-only stage labels; old failure phases remain usable for repair eligibility."""
STAGES=('build','geometry','editability','export','reimport')


def finalize(result):
    statuses=result.get('stage_statuses') or dict.fromkeys(STAGES,'not_reached')
    measurements=result.get('stage_measurements') or dict.fromkeys(STAGES)
    verification=result.get('verification')
    if verification is not None or result.get('verification_pid') is not None:
        statuses['reimport']='pass' if result.get('verification_pass') is True else 'fail'
        measurements['reimport']=verification
    result['stage_statuses']=statuses;result['stage_measurements']=measurements
    if result.get('probe_status')=='exception':code=None
    elif result.get('geometry_ok') is False:code='geometry_pre_export'
    elif result.get('geometry_ok') is True and result.get('editability_ok') is False:code='editability_pre_export'
    elif statuses['export']=='fail' or result.get('failed_phase')=='export':code='export_failure'
    elif statuses['reimport']=='fail':code='reimport_verification_fail'
    else:code=None
    result['failure_class_v3']=code
    return result
