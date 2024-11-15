params = ','
masks = []
for region in ['SR_fail','SR_pass','VR_fail','VR_pass']:
    for channel in ['LOW','SIG','HIGH']:
        if ('SR' in region):
            masks.append(f'mask_{region}_{channel}=0')
        else:
            masks.append(f'mask_{region}_{channel}=1')
print(params.join(masks))
